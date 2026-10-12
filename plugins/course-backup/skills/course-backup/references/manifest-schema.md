# manifest.json 格式

`scripts/download_manifest.py` 唯一的輸入。所有平台適配的目標都是產出這個格式。

```json
{
  "course": "範例課程",
  "source": "example-school.example.com",
  "generatedAt": "2026-01-01T00:00:00Z",
  "chapters": [
    {
      "title": "CH1 入門",
      "units": [
        {
          "title": "1-1 課程導覽",
          "duration": 1324.5,
          "notes": "平台上的單元文字說明，可省略",
          "videos": [
            {"type": "hls", "url": "https://.../master.m3u8?簽名", "prefer": "1080"},
            {"type": "mp4", "url": "https://.../video.mp4?簽名"},
            {"type": "youtube", "url": "https://www.youtube.com/watch?v=xxxx"}
          ],
          "captions": [
            {"lang": "zh", "url": "https://.../zh.vtt?簽名"}
          ],
          "materials": [
            {"name": "講義1-1.pdf", "size": 1234567, "url": "https://s3.../x.pdf?簽名"}
          ]
        }
      ]
    }
  ]
}
```

規則：

- `duration` 單位秒，可省略；有給才會做時長比對。
- `videos` 一個單元通常一支；多支時檔名會加 `_2`、`_3`。
- `hls.prefer` 是變體選擇關鍵字（`1080`／`720`），找不到就取 master 裡第一個變體。
- `hls` 的 `url` 必須是 master playlist 的**完整可用網址**（含簽名）；相對路徑的變體與 segment 會沿用同一段 query string，這是 CloudFront 簽名的常見作法。
- `materials` 的 `size` 用來驗證下載完整性，平台有給就一定要帶。
- `youtube` 型別交給 yt-dlp，字幕會一併抓（見 `youtube.md`），所以 `captions` 可留空。
