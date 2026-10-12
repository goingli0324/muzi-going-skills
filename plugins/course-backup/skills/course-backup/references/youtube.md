# YouTube 來源

適用：課程影片是 YouTube 播放清單、不公開（unlisted）影片、或課程頁內嵌的 YouTube 播放器。

## 先確認

- 需要 `yt-dlp`（`brew install yt-dlp`；YouTube 常改版，用前先 `yt-dlp -U` 或 `brew upgrade yt-dlp`）與 `ffmpeg`。
- 私人（private）影片 yt-dlp 抓不到，除非帶使用者瀏覽器 cookies：`--cookies-from-browser chrome`。這會讀取使用者 Chrome 的 cookie 檔，屬於使用者本人的登入狀態，用前要說一聲。
- 內嵌在課程頁的 YouTube 影片，先從頁面撈 `iframe[src*="youtube.com/embed/"]` 取得影片 id，再組成 `https://www.youtube.com/watch?v=<id>`。
- 有些內嵌影片設了「只能在特定網域播放」，yt-dlp 要加 `--referer <課程網址>`。

## manifest 寫法

```json
{"type": "youtube", "url": "https://www.youtube.com/watch?v=xxxx"}
```

`download_manifest.py` 對這個型別執行：

```bash
yt-dlp -f "bv*[height<=1080]+ba/b" --merge-output-format mp4 \
  --write-subs --write-auto-subs --sub-langs "zh-TW,zh-Hant,zh,zh-Hans,en" --sub-format vtt \
  -o "<單元檔名>.%(ext)s" "<url>"
```

抓到的字幕檔會被腳本改名成 `<單元>.zh.vtt` 並轉出 `.逐字稿.txt`。自動字幕（auto-subs）品質普通，仍算「有字幕」；要更好的逐字稿就走 Step 6 的 faster-whisper。

## 整份播放清單

使用者只給播放清單網址時，先列清單再產 manifest（每支影片一個單元）：

```bash
yt-dlp --flat-playlist -J "<playlist url>" > playlist.json
```

`entries[].title`、`entries[].id`、`entries[].duration` 直接對應 manifest 的 `title`／`url`／`duration`。章節就用播放清單標題當一章。
