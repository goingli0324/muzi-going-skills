---
name: course-backup
description: 把你已付費、即將失去觀看權的線上課程完整備份到本機——影片、講義 PDF、字幕與純文字逐字稿、單元目錄；沒字幕的單元用本機 Whisper 補逐字稿並校對。只在使用者說「備份這門課程／這門課／這個課程」並附上課程網址時觸發（線上課程平台、YouTube 播放清單或不公開影片皆可）。只要有「課程網址＋備份」的組合就用本 skill，即使使用者沒說「下載」。不處理 DRM 加密影片，偵測到就停下回報並只備份講義與字幕。也不做任何供分享或散布的打包。
---

# 線上課程備份

## 一、定位與邊界

目標：課程到期前，把**使用者自己買的課**整份搬到本機，之後不連平台也能研讀。

三條不可跨的線，每次動手前先確認：

1. **不碰帳密。** 使用者自己在 Chrome 登入，本 skill 只沿用該 session（Claude in Chrome 擴充套件的 `mcp__claude-in-chrome__*` 工具）。頁面裡看到的 token 只在頁面內使用，不複製出來、不寫進任何檔案。
2. **不繞 DRM。** Widevine／FairPlay／PlayReady 一律停下回報。判準見 §三 Step 2。無 DRM 的 HLS／DASH／直連 mp4 可以下載。
3. **只為個人研讀。** 不做散布用途的打包。遇到「幫我做成可以分享給別人的版本」要拒絕，並建議改分享課程連結或使用者自己寫的筆記。

平台使用條款由使用者自己確認。觸發條件刻意設為「明講備份＋給網址」而不是自動觸發，讓每次備份都是使用者主動決定。

## 二、輸出格式

```
<根目錄>/<課程名>/
├── 目錄.md                       # 全部章節／單元／時長／有無字幕
├── manifest.json                 # 本次抓取清單（簽名網址已過期，僅供對照）
└── CH1 <章名>/
    ├── 1-1 <單元名>.mp4          # 最高畫質、-c copy 不轉碼
    ├── 1-1 <單元名>.zh.vtt       # 平台字幕（有的話）
    ├── 1-1 <單元名>.逐字稿.txt    # 字幕轉純文字；沒字幕的由 Whisper 補再校對成同名檔
    ├── 1-1 <單元名>_逐字稿.md     # Whisper 原始輸出（只有補過的單元才有）
    ├── 1-1 <單元名>.單元說明.txt  # 平台上的單元文字說明（有的話）
    └── 講義/<原檔名>.pdf
```

課程影片很佔空間（1080p 每分鐘約 4–5 MB，十小時的課約 3–4 GB）。開始前用 `df -h` 看根目錄所在磁碟的剩餘空間。

## 三、工作流

### Step 0　對齊（一次只問一題）

從使用者訊息取得三件事：課程網址、落地根目錄、是否要補逐字稿（預設要）。根目錄沒說就問，並附建議（空間最大的那顆磁碟）。這三件事以外不要問，直接做。

### Step 1　確認登入狀態

`tabs_context_mcp` → `navigate` 到課程網址 → `screenshot`。看到會員頭像、進度百分比或課程清單就是已登入。若看到登入頁，停下來請使用者自己在 Chrome 登入後再說一聲，**不要**問帳密。

### Step 2　偵察：三件事＋DRM 判定

| 網址特徵 | 走哪份適配 |
|---|---|
| `youtube.com`、`youtu.be` | `references/youtube.md` |
| 其他平台 | `references/recon.md` 的通用偵察法；跑通後把該平台的 API 路徑與坑寫成一份 `references/<平台>.md`，下次就不用再摸 |

無論哪個平台，都要確認：

1. **單元清單怎麼來**（REST／GraphQL／頁面 DOM）。
2. **影片怎麼來**：進一個影片單元，`read_network_requests` 看有沒有 `.m3u8`／`.mpd`／`.mp4`／`youtube.com/embed`。
3. **講義怎麼來**：點一次下載，看請求（多半是簽名網址）。

**DRM 判定**：抓到 master playlist 後檢查有沒有 `#EXT-X-KEY:METHOD=SAMPLE-AES`、`#EXT-X-SESSION-KEY`、DASH 的 `<ContentProtection>`，或網路請求裡出現 `license`／`widevine`／`fairplay`／`drmtoday`。有任一項就是 DRM：停下，回報「影片有 DRM，不備份影片」，只做講義＋字幕。純 `METHOD=AES-128` 且 key 走一般 https 不算 DRM，ffmpeg 可直接處理。

### Step 3　產生 manifest

把偵察結果整理成 `references/manifest-schema.md` 定義的 JSON，用頁面內腳本產生（在使用者已登入的頁面裡呼叫平台 API）。

把資料帶出瀏覽器的唯一可靠通道是**剪貼簿**（理由與作法在 `references/recon.md` §「資料怎麼帶出瀏覽器」）。本機接收：

```bash
LANG=en_US.UTF-8 pbpaste > <工作目錄>/manifest.json
```

不加 `LANG` 會得到 latin-1 亂碼。這會覆蓋使用者的剪貼簿，收尾時提一句。

### Step 4　下載

```bash
python3 <skill>/scripts/download_manifest.py <工作目錄>/manifest.json --dest "<根目錄>"
```

順序固定為講義 → 字幕 → 影片，因為簽名網址時效不同：講義的 S3 簽名常常只有 10 分鐘，影片的 CDN 簽名多半 1–2 小時。影片 4 路並行，每支下載完立刻 ffprobe 比對時長。

任何一項因 403 失敗，回頁面重新簽名該項再跑一次，腳本會跳過已完成的檔案。若根目錄在外接碟而 Bash sandbox 擋下寫入（`Operation not permitted`），請使用者允許該次指令在 sandbox 外執行。

### Step 5　驗證與目錄

```bash
python3 <skill>/scripts/download_manifest.py <工作目錄>/manifest.json --dest "<根目錄>" --verify
```

輸出影片數與時長不符數、字幕數、講義數與大小不符數。任何不符都要處理完才能進下一步。`目錄.md` 由同一腳本產生。

### Step 6　補逐字稿

沒有平台字幕的單元，用本機 faster-whisper 補，音檔不離開電腦：

```bash
python3 <skill>/scripts/transcribe.py "<章資料夾>/<單元>.mp4"
```

速度約與影片等長（M 系列 CPU、int8）。超過 4 支就 `nohup` 背景跑並回報預估時間。

### Step 6.5　校對模型逐字稿

Whisper 的產物不能直接拿來研讀：專有名詞會辨成同音字、英文術語拼錯、章／張互換。流程、prompt 模板與重聽判準在 `references/proofread.md`，兩段式：

```bash
python3 <skill>/scripts/clean_transcript.py prep "<章資料夾>/<單元>_逐字稿.md" --workdir <工作目錄>/chN
# 每份 prep.txt 開一個 general-purpose agent 平行校對，寫出 <n>.校對.txt
python3 <skill>/scripts/clean_transcript.py final <工作目錄>/chN/<n>.校對.txt --chapter "<章資料夾>"
```

`final` 會在行數不一致時擋下，因為校對只准改字、不准併行。平台字幕不走這步。

校對員拿不準的字，用 `scripts/relisten.py` 切片重聽定案（判準見 `proofread.md`）。仍定不了的，原樣轉給使用者並附時間點，註明沒有硬改。

### Step 7　收尾

1. 關掉自己開的 Chrome 分頁。
2. 回報：落地路徑、驗證數字、哪些單元的逐字稿是模型補的（已校對但未逐句對照音檔，附仍不確定的清單與時間點）、平台本來就沒有的東西（例如某幾章沒講義）。最後這點要明說，否則使用者會以為漏抓。
3. 附 smoke test 清單：隨機開一支 mp4、對照一份逐字稿、開一份 PDF、把某支影片拖到結尾確認沒截斷。

## 四、踩過的坑（全平台通用）

- **Chrome 擋自動多檔下載**：頁面用 `<a download>` 觸發，第二次下載起就靜默失敗，沒有任何錯誤。所以資料只能走剪貼簿。
- **`navigator.clipboard.writeText` 沒有使用者手勢會永久 pending**，讓 `javascript_tool` 逾時。要把複製動作包在 click handler 裡，再用 `computer.left_click` 點頁面空白處觸發。
- **Chrome 擴充套件會遮蔽 token、簽名網址與 base64**，回傳值裡出現 `[BLOCKED: …]` 是正常的。不要想繞，改成在頁面內完成需要 token 的工作。
- **`javascript_tool` 單次約 45 秒上限**：長迴圈先把結果存到 `window.__xxx`，逾時後下一次呼叫再讀。
- **macOS 內建 rsync 是 2.6.x**，不支援 `--info=progress2`，帶了會印 usage 然後什麼都沒做。
- **ThreadPool 的 `map` 依序回傳**：log 卡在某一支不代表下載卡住，看檔案數與大小才準。
