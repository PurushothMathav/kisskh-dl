__author__ = 'PanguPlay'


import argparse
import os
from time import time
from datetime import datetime
from tqdm.auto import tqdm
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed

from Clients.KissKhClient import KissKhClient
from Utils.commons import load_yaml, colprint, colprint_init, pretty_time
from Utils.HLSDownloader import HLSDownloader
from Utils.BaseDownloader import BaseDownloader
import requests

def download_file(url, output_path, referer=None):
    headers = {'Referer': referer} if referer else {}
    with requests.get(url, stream=True, headers=headers) as r:
        r.raise_for_status()
        total = int(r.headers.get('content-length', 0))
        with open(output_path, 'wb') as f, tqdm(
            desc=os.path.basename(output_path),
            total=total,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))

def sanitize_title(title):
    return ''.join(c for c in title if c.isalnum() or c in [' ', '-', '_']).rstrip()

def prompt_episode_range(max_ep):
    inp = colprint('user_input', f"\nEnter episodes to download (ex: 1-5) [default=1-{max_ep}]: ", input_type='recurring', input_dtype='range')
    if not inp:
        return list(range(1, max_ep + 1))
    if '-' in inp:
        start, end = map(int, inp.split('-'))
        return list(range(start, end + 1))
    return [int(i) for i in inp.split(',') if i.isdigit()]

def prompt_resolution(available_res):
    inp = colprint('user_input', f"\nEnter download resolution {available_res} [default={available_res[-1]}]: ", input_type='recurring')
    return inp if inp in available_res else available_res[-1]
    
def download_single_episode(ep_data):
    """Download a single episode (to be called in parallel)"""
    ep_no, ep, chosen_res, target_dir, dl_config, client, series_title, args, position = ep_data
    
    if chosen_res not in ep['downloadLink']:
        return (ep_no, False, f"No {chosen_res}P available")
    
    try:
        link_info = ep['downloadLink'][chosen_res]
        ep['downloadLink'] = link_info['downloadLink']
        ep['duration'] = link_info['duration']
        ep['resolution_size'] = link_info['resolution_size']
        ep['filesize_mb'] = link_info.get('filesize_mb')
        ep['episodeName'] = f"{sanitize_title(series_title)} Episode {int(ep_no):02d} - {chosen_res}P.mp4"
        ep['out_dir'] = target_dir
        
        # Get subtitle data from client's udb_dict
        udb_data = client._get_udb_dict().get(ep_no, {})
        ep['subtitles'] = udb_data.get('subtitles', {})
        ep['encrypted_subs_details'] = udb_data.get('encrypted_subs_details', {})
        ep['refererLink'] = udb_data.get('refererLink', args.url)
        
        print(f"\n[Episode {ep_no}] Starting download: {ep['episodeName']}")
        start = time()
        
        # Create episode-specific download config
        episode_dl_config = dl_config.copy()
        episode_dl_config['download_dir'] = target_dir
        episode_dl_config['tqdm_position'] = position
        
        if link_info['downloadType'] == 'hls':
            downloader = HLSDownloader(episode_dl_config, ep)
            downloader.start_download(ep['downloadLink'])
        elif link_info['downloadType'] == 'mp4':
            downloader = BaseDownloader(episode_dl_config, ep)
            downloader.start_download(ep['downloadLink'])
        else:
            return (ep_no, False, f"Unknown download type: {link_info['downloadType']}")
        
        end = time()
        duration = pretty_time(int(end - start))
        return (ep_no, True, duration)
        
    except Exception as e:
        return (ep_no, False, str(e))    

def main():
    parser = argparse.ArgumentParser(description='Download series from kisskh.ovh')
    parser.add_argument('url', help='KissKh series page URL')
    args = parser.parse_args()

    config = load_yaml('config_kisskh.yaml')
    kisskh_config = config['Anime, Drama, Movies & TV Shows (Kisskh)']
    dl_config = config['DownloaderConfig']

    client = KissKhClient(kisskh_config)

    parsed_url = urlparse(args.url)
    query_params = parse_qs(parsed_url.query)
    series_id = query_params.get('id', [None])[0]

    if not series_id:
        raise ValueError("❌ Series ID not found in the URL. Please provide a link with '?id=####' at the end.")

    search_result = client._send_request(client.series_url + str(series_id), return_type='json')
    if not search_result:
        raise Exception("❌ Could not fetch series details from the URL.")

    target_series = {
        'id': series_id,
        'title': search_result['title'],
        'year': search_result['releaseDate'].split('-')[0],
        'country': search_result.get('country', 'Unknown'),
        'series_type': search_result.get('type', 'Unknown'),
        'status': search_result.get('status', 'Unknown'),
        'episodes': search_result.get('episodes', [])
    }

    print("\nFetching episode list...")
    episodes = client.fetch_episodes_list(target_series)

    if not episodes:
        raise Exception("❌ No episodes found for this series.")

    print("\nAvailable Episodes:")
    for ep in episodes:
        print(f"Episode {ep['episode']}: {ep['episodeName']}")

    selected_eps = prompt_episode_range(len(episodes))
    selected_episodes = [ep for ep in episodes if int(ep['episode']) in selected_eps]

    ep_ranges = {
        'start': min(ep['episode'] for ep in selected_episodes),
        'end': max(ep['episode'] for ep in selected_episodes),
        'specific_no': []
    }

    print("\nFetching available resolutions:")
    all_links = client.fetch_episode_links(episodes, ep_ranges)

    print(f"DEBUG: all_links keys = {list(all_links.keys())}")
    print(f"DEBUG: selected_eps = {selected_eps}")
    print(f"DEBUG: Episode 1 data = {all_links.get(1)}")

    download_links = {
        ep_no: data
        for ep_no, data in all_links.items()
        if int(str(ep_no)) in selected_eps
    }

    valid_links = {}
    for ep_no, ep_data in download_links.items():
        print(f"DEBUG: Checking Episode {ep_no} for stream data")
        if not isinstance(ep_data, dict) or len(ep_data) == 0:
            print(f"⚠️ Skipping Episode {ep_no}: No resolution info available.")
            continue
        valid_links[ep_no] = { 'downloadLink': ep_data }

    if not valid_links:
        raise Exception("❌ No valid episodes found for the selected range.")

    available_res = set()
    for ep_data in valid_links.values():
        available_res.update(ep_data['downloadLink'].keys())

    if not available_res:
        raise Exception("❌ No available resolutions found for the selected episodes.")

    chosen_res = prompt_resolution(sorted(available_res))

    print("\nReady to download the following episodes:")
    for ep_no, ep_data in valid_links.items():
        if chosen_res not in ep_data['downloadLink']:
            print(f"⚠️ Skipping Episode {ep_no}: No link for {chosen_res}P")
            continue
        link = ep_data['downloadLink'][chosen_res]['downloadLink']
        print(f"Episode {ep_no} | {chosen_res}P | Link found [{link}]")

    confirm = input("\nProceed to download (y|n)? ").strip().lower()
    if confirm != 'y':
        print("Aborted.")
        return

    title = sanitize_title(search_result['title'])
    target_dir = os.path.join(dl_config['download_dir'], f"{title} ({search_result['releaseDate'].split('-')[0]})")
    os.makedirs(target_dir, exist_ok=True)

    # Prepare episode tasks for parallel download
    max_workers = dl_config.get('max_parallel_downloads', 2)
    episode_tasks = [
        (ep_no, ep, chosen_res, target_dir, dl_config, client, title, args, idx % max_workers)
        for idx, (ep_no, ep) in enumerate(valid_links.items())
    ]
    
    print(f"\n{'='*70}")
    print(f"Starting parallel download of {len(episode_tasks)} episode(s)")
    print(f"Max parallel downloads: {max_workers}")
    print(f"{'='*70}\n")
    
    # Download episodes in parallel using ThreadPoolExecutor
    completed = 0
    failed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix='episode-dl-') as executor:
        # Submit all tasks
        future_to_episode = {
            executor.submit(download_single_episode, task): task[0] 
            for task in episode_tasks
        }
        
        # Process completed downloads as they finish
        for future in as_completed(future_to_episode):
            ep_no = future_to_episode[future]
            try:
                episode_num, success, message = future.result()
                if success:
                    print(f"\n✅ [Episode {episode_num}] Completed in {message}")
                    completed += 1
                else:
                    print(f"\n❌ [Episode {episode_num}] Failed: {message}")
                    failed += 1
            except Exception as e:
                print(f"\n❌ [Episode {ep_no}] Exception: {str(e)}")
                failed += 1
    
    print(f"\n{'='*70}")
    print(f"Download Summary: {completed} successful, {failed} failed")
    print(f"{'='*70}")
    print("\nAll downloads complete!")

if __name__ == '__main__':
    colprint_init(False)
    main()
