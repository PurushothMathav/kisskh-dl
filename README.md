# 📥 KissKh Downloader

A powerful Python script to **download full episodes (video + subtitles)** from [KissKh](https://kisskh.ovh) — supports both **HLS (.m3u8)** streams and **direct MP4** links, along with multi-language subtitles via API/JS page scraping.

---

## 📂 Project Structure

```
kisskh-dl/
├── kisskh-dl.py                # 🚀 Main downloader script (entry point)
├── config_kisskh.yaml          # ⚙️ Configuration for API keys, endpoints, and download directory
├── requirements.txt            # 📦 Required Python dependencies
├── Clients/
│   └── KissKhClient.py         # 🔌 Client wrapper to interact with KissKh API
|   └── BaseClient.py 
├── Utils/
│   ├── commons.py              # 🛠️ Utility functions (color printing, YAML loader, retries, etc.)
│   ├── BaseDownloader.py       # 📥 Abstract downloader (shared base class)
│   └── HLSDownloader.py        # 🌐 Downloads M3U8 stream using segment fetching and FFmpeg conversion
```

---

## 🧰 Features

- ✅ Download from **KissKh** using **URL or ID**
- ✅ **Choose episode range** and **resolution**
- ✅ Automatically detects whether stream is `HLS` or `MP4`
- ✅ Supports **multi-language subtitles** (auto fetched from JS-rendered token)
- ✅ Subtitles are **soft-muxed** into the output `.mp4` using FFmpeg
- ✅ Reliable with **progress bars**, **error handling**, and **debug logging**

---

## 📦 Requirements

- Python 3.8+
- Google Chrome installed
- ChromeDriver installed and in PATH (for subtitle scraping)
- FFmpeg installed and in PATH
- Internet connection (obviously 😉)

---

## 📋 Installation

```bash
git clone https://github.com/PurushothMathav/kisskh-dl.git
cd kisskh-dl

# Install Python dependencies
pip install -r requirements.txt
```

---

## 🔧 Configuration

Edit the `config_kisskh.yaml` file to set:

```yaml
DownloaderConfig:
  download_dir: D:/kisskh dl/Videos   # 💾 Your desired download output folder

Anime, Drama, Movies & TV Shows (Kisskh):
  base_url: https://kisskh.ovh
  api_url: https://kisskh.ovh/api
  video_stream_url: https://kisskh.app/Drama
  subtitles_url: api/Sub/{id}?kkey=
```

---

## 🚀 Usage

### ▶️ Run the downloader with a show URL:

```bash
python kisskh-dl.py "https://kisskh.ovh/Drama/The-Demon-Hunter-s-Romance?id=7647"
```

### 🧠 The script will:

1. Fetch metadata and episode list
2. Ask you which episodes to download (e.g., `1-3`)
3. Ask for the resolution (e.g., `720`)
4. Automatically fetch subtitle token (`kkey`) using **headless Chrome**
5. Download video and subtitles
6. Soft-mux subtitles into the final `.mp4`

---

## 🌐 Subtitle Support

Subtitles are automatically fetched using a **Selenium-based browser instance** that loads the episode page (e.g. `Episode-10?id=7647&ep=180316`) and extracts the encryption token (`kkey`). This is then used to fetch the JSON subtitle metadata and download `.srt` files.

---

## 🛠 Advanced Notes

- For `.m3u8` streams:
  - Segments are downloaded one-by-one and stitched using FFmpeg
  - Works even for encrypted HLS (if key is public)

- For `.mp4` direct links:
  - Downloaded directly via streaming requests
  - Referer header is preserved

- Subtitles:
  - Soft-muxed as `mov_text` into MP4 container (no hard-burn)

---

## 📌 Troubleshooting

- ❌ `Subtitle token not found`: Check network block/firewall or outdated ChromeDriver.
- ❌ `403 Forbidden`: Ensure token URL is valid, or retry (might be IP-sensitive).
- 🛠 Use `DEBUG` prints in the script for more insight (search for `DEBUG:` in code).

---

## 🤝 Credits

- Inspired by `udb.py` and adapted to a full-featured standalone downloader.
- Reverse-engineered logic from `parallel-fetch-subtitles.js` and `fetch-drama-data.js`.

---

## 📜 License

MIT — free to use, share and modify. Give credit if helpful!
