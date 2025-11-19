# KissKh Downloader

A powerful, feature-rich command-line tool to download Asian dramas, movies, and anime from KissKh with multi-threaded downloads, automatic subtitle support, and adaptive quality selection.

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## ✨ Features

- 🔍 **Smart Search** - Search dramas by keyword or use direct URLs
- 📥 **Multi-threaded Downloads** - Download multiple episodes simultaneously
- 🎬 **Adaptive Quality** - Automatically selects best available resolution
- 📝 **Subtitle Support** - Auto-downloads and embeds subtitles with encryption handling
- 🌐 **Multiple Languages** - Supports English, Indonesian, Malay, Arabic, Hindi, and more
- 🎯 **Smart Episode Selection** - Download specific episodes or ranges
- 🎁 **Special Episodes** - Handles bonus content and OVAs (36.1, 36.2, etc.)
- 🔄 **Auto-retry** - Handles network failures with exponential backoff
- 📊 **Progress Tracking** - Real-time download progress with tqdm
- 🎨 **Colorful Output** - Clear, colored terminal output for better UX

## 🎯 What Makes This Different

- **Adaptive Resolution Selection** - If your preferred quality isn't available, it automatically picks the closest alternative
- **Parallel Episode Downloads** - Download multiple episodes at once with configurable workers
- **Default Subtitle Language** - English subtitles enabled by default in all players
- **Special Episode Handling** - Gracefully handles bonus content with decimal episode numbers
- **Smart Retry Logic** - Connection issues? The script automatically retries with increasing delays

## 📋 Requirements

- Python 3.8+
- ffmpeg (for video/subtitle processing)
- Required Python packages (see [Installation](#-installation))

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/PurushothMathav/kisskh-dl.git
cd kisskh-dl
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install FFmpeg

**Windows:**
```bash
# Using Chocolatey
choco install ffmpeg

# Or download from: https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

### 4. Configure Settings

Edit `config_kisskh.yaml` to set your preferences:
```yaml
Anime, Drama, Movies & TV Shows (Kisskh):
  download_dir: D:\kisskh dl\Videos        # Your download directory
  request_timeout: 30
  alternate_resolution_selector: 'closest'  # 'closest', 'highest', or 'lowest'

DownloaderConfig:
  download_dir: D:\kisskh dl\Videos         # For Mobile "/sdcard/Download/"
  temp_download_dir: auto
  concurrency_per_file: 8                   # Threads per file (segments/chunks)
  request_timeout: 30
  max_parallel_downloads: 2                 # Download 2 episodes simultaneously
  use_http_client: false

LoggerConfig:
  log_level: INFO
  log_dir: logs
  max_log_size_in_kb: 100
  log_backup_count: 3
  log_retention_days: 7
```

## ⭐ Android Termux Keypoints

### Download Location Set using Nano
```bash
# Use Nano Editor
pkg install nano
nano config_kisskh.yaml

# Change download_dir location
download_dir: "/sdcard/Download/"

# Save and exit
Press Ctrl + X
Press Y to confirm saving the changes
Press Enter to confirm the filename
```

### Download Location Set using Vim
```bash
# Use Vim Editor
pkg install vim
vim config_kisskh.yaml

# Edit file
vim starts in "normal" mode. To start editing, press the i key to enter "insert" mode.

# Change download_dir location
download_dir: "/sdcard/Download/"

# Save and exit
Press the Esc key to exit "insert" mode and return to "normal" mode.
Type :wq (write and quit) and press Enter
```

## 📖 Usage

### Method 1: Search by Keyword
```bash
# Search for a drama
python kisskh-dl.py "Demon Hunter"
python kisskh-dl.py -s "Demon Hunter"

# Interactive search (prompts for keyword)
python kisskh-dl.py -s
python kisskh-dl.py
```

### Method 2: Direct URL
```bash
python kisskh-dl.py "https://kisskh.ovh/Drama/The-Demon-Hunter-s-Romance?id=7647"
```

### Interactive Example
```bash
$ python kisskh-dl.py "Demon Hunter"

🔍 Searching for: Demon Hunter
======================================================================
-------------- Asian Drama --------------
1: The Demon Hunter's Romance | Country: China
   | Episodes: 42 | Released: 2025 | Status: Ongoing

2: Demon Hunter Season 2 | Country: China
   | Episodes: 24 | Released: 2024 | Status: Complete

======================================================================

Select drama number (1-2) or 'q' to quit: 1

✅ Selected: The Demon Hunter's Romance (2025)

Fetching episode list...

Available Episodes:
Episode 1: The Demon Hunter's Romance Episode 1
Episode 2: The Demon Hunter's Romance Episode 2
...
Episode 42: The Demon Hunter's Romance Episode 42

Enter episodes to download (ex: 1-5) [default=1-42]: 20-22

Fetching available resolutions:
Episode: 20 (duration: 00:47:51) | 536P (1280x536) [~361 MB]
Episode: 21 (duration: 00:47:00) | 536P (1280x536) [~336 MB]
Episode: 22 (duration: 00:46:03) | 536P (1280x536) [~341 MB]

Enter download resolution ['536', '720'] [default=720]: 536

Ready to download the following episodes:
Episode 20 | ✓ 536P | Link: https://...
Episode 21 | ✓ 536P | Link: https://...
Episode 22 | ✓ 536P | Link: https://...

Proceed to download (y|n)? [default=y]: 

======================================================================
Starting parallel download of 3 episode(s)
Max parallel downloads: 2
======================================================================

Downloading Episode-20: 100%|████████████████| 361M/361M [00:58<00:00, 6.2MiB/s]
Downloading Episode-21: 100%|████████████████| 336M/336M [00:54<00:00, 6.3MiB/s]

✅ [Episode 20] Completed in 00:00:58 [536P]
✅ [Episode 21] Completed in 00:00:54 [536P]

Downloading Episode-22: 100%|████████████████| 341M/341M [00:55<00:00, 6.2MiB/s]

✅ [Episode 22] Completed in 00:00:55 [536P]

======================================================================
Download Summary: 3 successful, 0 failed
======================================================================

All downloads complete!
```

## 🎛️ Advanced Configuration

### Performance Tuning

**For Fast Internet (100+ Mbps):**
```yaml
DownloaderConfig:
  concurrency_per_file: 16
  max_parallel_downloads: 3
```

**For Slow/Unstable Internet:**
```yaml
DownloaderConfig:
  concurrency_per_file: 4
  max_parallel_downloads: 1
  request_timeout: 60
```

**For Maximum Speed:**
```yaml
DownloaderConfig:
  concurrency_per_file: 16
  max_parallel_downloads: 4
```

### Resolution Selection Strategies

- **`closest`** - Selects nearest available resolution (default)
- **`highest`** - Always picks highest quality available
- **`lowest`** - Always picks lowest quality (saves bandwidth)

## 📁 Project Structure
```
kisskh-dl/
├── kisskh-dl.py              # Main script
├── config_kisskh.yaml        # Configuration file
├── requirements.txt          # Python dependencies
├── Clients/
│   ├── BaseClient.py         # Base client with common methods
│   └── KissKhClient.py       # KissKh-specific implementation
└── Utils/
    ├── commons.py            # Common utilities and helpers
    ├── BaseDownloader.py     # Base downloader for MP4 files
    └── HLSDownloader.py      # HLS stream downloader
```

## 🔧 Troubleshooting

### Connection Reset Errors
The script automatically retries with exponential backoff. If issues persist:
- Wait a few minutes and try again
- Check if the site is accessible in your browser
- Try using a VPN

### Subtitles Not Showing in VLC
The script sets English as default. If still not showing:
1. **VLC Desktop**: Tools → Preferences → Subtitles/OSD → Enable "Enable sub-pictures"
2. **VLC Mobile**: Settings → Subtitles → Enable "Subtitles"

### FFmpeg Not Found
Make sure ffmpeg is in your system PATH:
```bash
ffmpeg -version
```

### Permission Errors
Run terminal/command prompt as administrator or check folder permissions.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for educational purposes only. Please respect copyright laws and only download content you have the right to access. The developers are not responsible for any misuse of this software.

## 🙏 Credits

Inspired by [udb.py](https://github.com/Prudhvi-pln/udb) by **Prudhvi PLN** and adapted into a full-featured standalone downloader with enhanced capabilities.

Special thanks to:
- **Prudhvi PLN** for the original UDB framework and architecture
- The open-source community for various libraries used in this project
- Contributors who help improve this tool

## 📮 Support

If you encounter any issues or have suggestions:
- Open an [Issue](https://github.com/PurushothMathav/kisskh-dl/issues)
- Check existing issues for solutions
- Star ⭐ this repository if you find it useful!

## 🗺️ Roadmap

- [ ] GUI interface
- [ ] Download queue management
- [ ] Resume incomplete downloads
- [ ] Batch download from text file
- [ ] Integration with Plex/Jellyfin
- [ ] Automatic quality selection based on internet speed
- [ ] Discord/Telegram notifications

---

**Made with ❤️ for drama enthusiasts**
