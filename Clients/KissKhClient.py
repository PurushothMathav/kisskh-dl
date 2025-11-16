__author__ = 'Prudhvi PLN'

import re
import os
import logging
from quickjs import Context as quickjsContext
from urllib.parse import quote_plus

from Clients.BaseClient import BaseClient


class KissKhClient(BaseClient):
    '''
    All-in-one Client for kisskh site
    '''
    # step-0
    def __init__(self, config, session=None):
        self.base_url = config.get('base_url', 'https://kisskh.ovh/')
        self.search_url = self.base_url + config.get('search_url', 'api/DramaList/Search?q=')
        self.series_url = self.base_url + config.get('series_url', 'api/DramaList/Drama/')
        self.episode_url = self.base_url + config.get('episode_url', 'api/DramaList/Episode/{id}.png?kkey=')
        self.subtitles_url = self.base_url + config.get('subtitles_url', 'api/Sub/{id}?kkey=')
        self.preferred_urls = config['preferred_urls'] if config.get('preferred_urls') else []
        self.blacklist_urls = config['blacklist_urls'] if config.get('blacklist_urls') else []
        self.selector_strategy = config.get('alternate_resolution_selector', 'lowest')
        self.hls_size_accuracy = config.get('hls_size_accuracy', 0)
        super().__init__(config.get('request_timeout', 30), session)
        self.logger.debug(f'KissKh Drama client initialized with {config = }')
        self.token_generation_js_code = None
        self.quickjs_context = None
        # site specific details required to create token. Check dev-notes for more details.
        self.subGuid = "VgV52sWhwvBSf8BsM3BRY9weWiiCbtGp"
        self.viGuid = "62f176f3bb1b5b8e70e39932ad34a0c7"
        self.appVer = "2.8.10"
        self.platformVer = 4830201
        self.appName = "kisskh"
        # key and iv for decrypting subtitles for txt. Source: https://github.com/debakarr/kisskh-dl/issues/14#issuecomment-1862055123
        self.DECRYPT_SUBS_KEY = b'8056483646328763'
        self.DECRYPT_SUBS_IV = b'6852612370185273'
        # new key & iv for decrypting subtitles for txt1, as on Feb-13, 2025. Check your dev-notes for more details.
        self.DECRYPT_SUBS_KEY2 = b'AmSmZVcH93UQUezi'
        self.DECRYPT_SUBS_IV2 = b'ReBKWW8cqdjPEnF6'
        # key & iv for decrypting subtitles, default encryption.
        self.DECRYPT_SUBS_KEY3 = b'sWODXX04QRTkHdlZ'
        self.DECRYPT_SUBS_IV3 = b'8pwhapJeC4hrS9hO'

    # step-1.1
    def _show_search_results(self, key, details):
        '''
        pretty print drama results based on your search
        '''
        line = f"{key}: {details.get('title')} | Country: {details.get('country')}" + \
                f"\n   | Episodes: {details.get('episodesCount', 'NA')} | Released: {details.get('year')} | Status: {details.get('status')}"
        self._colprint('results', line)

    # step-4.1
    def _get_token(self, episode_id, uid):
        '''
        create token required to fetch stream & subtitle links
        '''
        # js code to generate token from kisskh site
        if self.token_generation_js_code is None:
            self.logger.debug('Fetching token generation js code...')
            soup = self._get_bsoup(self.base_url + 'index.html')
            common_js_url = self.base_url + [ i['src'] for i in soup.select('script') if i.get('src') and 'common' in i['src'] ][0]
            self.token_generation_js_code = self._send_request(common_js_url)

        # quickjs context for evaluating js code
        if self.quickjs_context is None:
            self.logger.debug('Creating quickjs context...')
            self.quickjs_context = quickjsContext()

        # evaluate js code to generate token
        self.logger.debug(f'Evaluating js code to generate token using {episode_id = } and {uid = }')
        token = self.quickjs_context.eval(self.token_generation_js_code + f'_0x54b991({episode_id}, null, "2.8.10", "{uid}", 4830201,  "kisskh", "kisskh", "kisskh", "kisskh", "kisskh", "kisskh")')
        return token

    # step-1
    def search(self, keyword, search_limit=5):
        '''
        search for drama based on a keyword
        '''
        # search type codes
        search_types = {
            # '0': 'all',
            '1': 'Asian Drama',
            '2': 'Asian Movies',
            '3': 'Anime',
            '4': 'Hollywood'
        }
        idx = 1
        search_results = {}
        search_type = None

        # check if search type is provided
        try:
            if '>' in keyword:
                search_type = [ k for k,v in search_types.items() if keyword.split('>')[0].strip().lower() in v.lower() ][0]
                keyword = keyword.split('>')[1].strip()
                search_limit = search_limit * 2
        except:
            pass

        # url encode search keyword
        search_key = quote_plus(keyword)

        for code, type in search_types.items():
            if search_type and search_type != code:
                continue
            self._colprint('blurred', f"-------------- {type} --------------")
            self.logger.debug(f'Searching for {type} with keyword: {keyword}')
            search_url = self.search_url + search_key + '&type=' + str(code)
            search_data = self._send_request(search_url, return_type='json')[:search_limit]
            # if len(search_data) == 0:
            #     self.logger.error('Nothing here')

            # Get basic details available from the site
            for result in search_data:
                series_id = result['id']
                self.logger.debug(f'Fetching additional details for series_id: {series_id}')
                series_data = self._send_request(self.series_url + str(series_id), return_type='json')
                item = {
                    'title': series_data['title'],
                    'series_id': series_id,
                    'country': series_data['country'],
                    'episodesCount': series_data['episodesCount'],
                    'series_type': series_data['type'],
                    'status': series_data['status'],
                    'episodes': series_data['episodes']
                }
                try:
                    item['year'] = series_data['releaseDate'].split('-')[0]
                except:
                    item['year'] = 'XXXX'

                # Add index to every search result
                search_results[idx] = item
                self._show_search_results(idx, item)
                idx += 1

        return search_results

    # step-2
    def fetch_episodes_list(self, target):
        '''
        fetch episode links as dict containing link, name
        '''
        all_episodes_list = []
        episodes = target['episodes']

        self.logger.debug(f'Extracting episode details for {target["title"]}')
        for episode in episodes:
            ep_no = int(episode['number']) if str(episode['number']).endswith('.0') else episode['number']
            ep_name = f"{target['title']} Movie" if target['series_type'].lower() == 'movie' else f"{target['title']} Episode {ep_no}"
            all_episodes_list.append({
                'episode': ep_no,
                'episodeName': self._windows_safe_string(ep_name),
                'episodeId': episode['id'],
                'episodeSubs': episode['sub']
            })

        return all_episodes_list[::-1]   # return episodes in ascending

    # step-3
    def show_episode_results(self, items, *predefined_range):
        '''
        pretty print episodes list from fetch_episodes_list
        '''
        start, end = self._get_episode_range_to_show(items[0].get('episode'), items[-1].get('episode'), predefined_range[1], threshold=24)
        display_prefix = 'Movie' if items[0].get('episodeName').endswith('Movie') else 'Episode'

        for item in items:
            if item.get('episode') >= start and item.get('episode') <= end:
                fmted_name = re.sub(r'\b(\d$)', r'0\1', item.get('episodeName'))
                self._colprint('results', f"{display_prefix}: {fmted_name}")

    # step-4
    def fetch_episode_links(self, episodes, ep_ranges):
        '''
        fetch only required episodes based on episode range provided
        '''
        download_links = {}
        ep_start, ep_end, specific_eps = ep_ranges['start'], ep_ranges['end'], ep_ranges.get('specific_no', [])
        display_prefix = 'Movie' if episodes[0].get('episodeName').endswith('Movie') else 'Episode'

        for episode in episodes:
            # self.logger.debug(f'Current {episode = }')

            if (float(episode.get('episode')) >= ep_start and float(episode.get('episode')) <= ep_end) or (float(episode.get('episode')) in specific_eps):
                self.logger.debug(f'Processing {episode = }')

                self.logger.debug('Fetching stream token')
                token = self._get_token(episode.get('episodeId'), self.viGuid)
                self.logger.debug(f'Fetching stream link')
                dl_links = self._send_request(self.episode_url.format(id=str(episode.get('episodeId'))) + token, return_type='json')
                if dl_links is None:
                    self.logger.warning(f'Failed to fetch stream link for episode: {episode.get("episode")}')
                    continue
                link = dl_links.get('Video')
                self.logger.debug(f'Extracted stream link: {link = }')

                # skip if no stream link found
                if link is None:
                    continue

                # check if link has countdown timer for upcoming releases
                if 'tickcounter.com' in link:
                    self.logger.debug(f'Episode {episode.get("episode")} is not released yet')
                    self._show_episode_links(episode.get('episode'), {'error': 'Not Released Yet'}, display_prefix)
                    continue

                # add episode details & stream link to udb dict
                self._update_udb_dict(episode.get('episode'), episode)
                self._update_udb_dict(episode.get('episode'), {'streamLink': link, 'refererLink': self.base_url})

                # get subtitles dictionary (key:value = language:link) and add to udb dict
                if episode.get('episodeSubs', 0) > 0:
                    self.logger.debug('Subtitles found. Fetching subtitles token')
                    token = self._get_token(episode.get('episodeId'), self.subGuid)
                    self.logger.debug('Fetching subtitles for the episode...')
                    subtitles_raw = self._send_request(self.subtitles_url.format(id=str(episode.get('episodeId'))) + token, return_type='json')
                    
                    # ✅ Store both URL and default flag
                    subtitles = { sub['label']: {'src': sub['src'], 'default': sub.get('default', False)} for sub in subtitles_raw }
                    self._update_udb_dict(episode.get('episode'), {'subtitles': subtitles})
                    
                    # ✅ Store which language is default
                    default_subtitle_lang = next((sub['label'] for sub in subtitles_raw if sub.get('default', False)), None)
                    if default_subtitle_lang:
                        self._update_udb_dict(episode.get('episode'), {'default_subtitle_lang': default_subtitle_lang})
                    # check if subtitles are encrypted and add decryption details to udb dict
                    # every subtitle can have it's own encryption type. So, check all subtitles for encryption and add decryption details to udb dict
                    encrypted_subs_details = {}
                    for k, v in subtitles.items():
                        self.logger.debug(f'Checking encryption type for {k} language...')
                        # ✅ Extract URL from dict format
                        sub_url = v['src'] if isinstance(v, dict) else v
                        encryption_type = sub_url.split('?')[0].split('.')[-1]
                        if encryption_type == 'txt':
                            encrypted_subs_details[k] = {'key': self.DECRYPT_SUBS_KEY, 'iv': self.DECRYPT_SUBS_IV, 'decrypter': self._aes_decrypt}
                        elif encryption_type == 'txt1':
                            encrypted_subs_details[k] = {'key': self.DECRYPT_SUBS_KEY2, 'iv': self.DECRYPT_SUBS_IV2, 'decrypter': self._aes_decrypt}
                        elif encryption_type == 'srt':
                            continue    # no encryption
                        else:
                            encrypted_subs_details[k] = {'key': self.DECRYPT_SUBS_KEY3, 'iv': self.DECRYPT_SUBS_IV3, 'decrypter': self._aes_decrypt}  # use default encryption

                    if encrypted_subs_details:
                        self.logger.debug(f'Encrypted subtitles found. Adding decryption details to udb dict...')
                        self._update_udb_dict(episode.get('episode'), {'encrypted_subs_details': encrypted_subs_details})

                # get actual download links
                m3u8_links = [{'file': link, 'type': 'hls'}] if link.split('?')[0].endswith('.m3u8') else [{'file': link, 'type': 'mp4'}]
                self.logger.debug(f'Fetching resolution streams from the stream link...')
                try:
                    m3u8_links = self._get_download_links(m3u8_links, self.base_url, self.preferred_urls, self.blacklist_urls)
                    self.logger.debug(f'Extracted {m3u8_links = }')
                except Exception as e:
                    self.logger.error(f'Failed to extract download links for episode: {episode.get("episode")}. Error: {e}')
                    continue

                download_links[episode.get('episode')] = m3u8_links
                self._show_episode_links(episode.get('episode'), m3u8_links, display_prefix)

        return download_links

    # step-5
    def set_out_names(self, target_series):
        drama_title = self._windows_safe_string(target_series['title'])
        # set target output dir
        target_dir = drama_title if drama_title.endswith(')') else f"{drama_title} ({target_series['year']})"

        return target_dir, None

    def download_and_save_subtitles(self, episode, out_dir, prefer_langs=None, referer=None):
        """
        Download available subtitles for the given `episode` dict and save them under out_dir.
        - episode: episode dict returned by the client (should contain 'subtitles' and optionally 'encrypted_subs_details')
        - out_dir: directory where to save subtitle files (must exist or will be created)
        - prefer_langs: optional list of language codes/names to prefer (e.g. ['English','en','eng'])
        - referer: optional referer header to pass when fetching (use same referer as the video)
        Returns: dict mapping language -> saved_filepath (for successful downloads)
        """
        if not episode:
            return {}

        subtitles = episode.get('subtitles') or {}
        enc_details = episode.get('encrypted_subs_details') or {}

        if not subtitles:
            self.logger.debug("No subtitles metadata for episode %s", episode.get('episode'))
            return {}

        os.makedirs(out_dir, exist_ok=True)
        saved = {}

        # helper to pick languages if prefer_langs provided
        langs = list(subtitles.keys())
        if prefer_langs:
            # try keep preferred order, but still include others afterwards
            ordered = []
            for p in prefer_langs:
                for l in langs:
                    if p.lower() in l.lower() and l not in ordered:
                        ordered.append(l)
            for l in langs:
                if l not in ordered:
                    ordered.append(l)
            langs = ordered

        for lang in langs:
            sub_url = subtitles.get(lang)
            if not sub_url:
                continue
            try:
                # fetch raw bytes
                raw = self._send_request(sub_url, referer=referer, return_type='bytes', silent=True)
                if raw is None:
                    self.logger.warning("Subtitle fetch returned None for %s (%s)", episode.get('episode'), lang)
                    continue

                # Determine whether this language is encrypted (client previously stored decryption details)
                dec_info = enc_details.get(lang)
                content_text = None

                if dec_info:
                    # expect dec_info has keys 'key', 'iv', 'decrypter' (the client sets these earlier)
                    # raw might be binary or base64 text depending on server; our decryptor expects a base64 string
                    try:
                        # convert bytes -> str first
                        raw_text = raw.decode('utf-8', errors='ignore').strip()
                        # call the decrypter. Most clients use self._aes_decrypt(base64str, key, iv)
                        key = dec_info.get('key')
                        iv = dec_info.get('iv')
                        decrypter = dec_info.get('decrypter', getattr(self, "_aes_decrypt", None))
                        if not decrypter:
                            raise RuntimeError("No decrypter available for encrypted subtitles")
                        # some code stores the decrypter as a function or as a string; handle both:
                        if callable(decrypter):
                            content_text = decrypter(raw_text, key, iv)
                        else:
                            # fallback to client's default method
                            content_text = self._aes_decrypt(raw_text, key, iv)
                    except Exception as e:
                        self.logger.warning("Failed to decrypt subtitle for %s %s: %s", episode.get('episode'), lang, e)
                        continue
                else:
                    # not encrypted - treat as text (vtt/srt)
                    try:
                        content_text = raw.decode('utf-8')
                    except Exception:
                        # binary fallback
                        content_text = raw.decode('utf-8', errors='ignore')

                if not content_text:
                    self.logger.warning("No subtitle content for %s %s", episode.get('episode'), lang)
                    continue

                # Decide extension: prefer original URL ext (vtt/srt/txt), otherwise default to .vtt
                ext = os.path.splitext(sub_url.split('?')[0])[1].lower().strip('.')
                if ext not in ('vtt', 'srt', 'txt'):
                    ext = 'vtt'  # default fallback

                # if encrypted txt variants may actually contain webvtt or srt text after decryption
                filename_base = self._windows_safe_string(episode.get('episodeName') or f"ep{episode.get('episode')}")
                # Normalize language tag for file name
                lang_tag = lang.replace(' ', '_').replace('/', '_')
                out_name = os.path.join(out_dir, f"{filename_base}.{lang_tag}.{ext}")

                with open(out_name, 'w', encoding='utf-8') as fh:
                    fh.write(content_text)

                self.logger.info("Saved subtitle: %s (%s)", out_name, lang)
                saved[lang] = out_name

            except Exception as e:
                self.logger.warning("Subtitle download failed for %s %s. Error: %s", episode.get('episode'), lang, e)

        return saved
