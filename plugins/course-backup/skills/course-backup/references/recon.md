# 通用偵察法（遇到沒有適配檔的平台時）

目標是回答三個問題：單元清單從哪來、影片從哪來、講義從哪來。全部用 `mcp__claude-in-chrome__*` 在使用者已登入的 Chrome 裡做。

## 1. 單元清單

1. 進課程頁，`get_page_text` 先拿到章節／單元標題的人可讀清單（之後對照用）。
2. `javascript_tool` 撈 `document.querySelectorAll('a[href]')`，找出指向單元頁的 href 樣式。
3. `read_network_requests` 找 `graphql`、`/api/`、`.json`。看到就記下路徑，接著在頁面內用 `fetch` 重打一次確認回應形狀。

## 2. 影片來源

點進一個影片單元，`read_network_requests`（先呼叫一次清空，再重新載入），依序找：

| 看到 | 代表 | 下載方式 |
|---|---|---|
| `.m3u8` | HLS | `download_manifest.py` 的 `hls` 型別 |
| `.mpd` | DASH | 先看有無同源 HLS；沒有就用 `yt-dlp` 直接吃 mpd 網址 |
| `.mp4` 帶簽名 | 直連 | `mp4` 型別 |
| `youtube.com/embed/<id>` | YouTube 內嵌 | `youtube` 型別（見 `youtube.md`） |
| `vimeo.com/video/<id>` | Vimeo 內嵌 | yt-dlp 通常可處理，需帶 `--referer` 課程網址 |
| `license`、`widevine`、`fairplay`、`drmtoday`、`.pssh` | **DRM** | 停下回報，不備份影片 |

抓到 master playlist 後在頁面內 `fetch` 一次，確認：`#EXT-X-KEY` 是否存在、有哪些 `RESOLUTION`、有無 `#EXT-X-MEDIA:TYPE=SUBTITLES`（字幕軌）。

## 3. 講義

在講義單元點一次下載按鈕，`read_network_requests` 看：

- 直接是 `s3.amazonaws.com`／`storage.googleapis.com` 帶簽名 → 記下**產生簽名的那個請求**（通常在它前面一筆，是 POST），要重現的是那個請求而不是簽名網址本身。
- 直接是靜態 CDN 網址 → 直接用。

## 需要 token 的 API

很多平台的 REST API 要 `Authorization: Bearer`，而 token 可能不在 localStorage（有的平台把它內嵌在首頁 HTML 的全域變數裡）。不要去找 token 在哪，改用**攔截**：

```js
const os = XMLHttpRequest.prototype.setRequestHeader;
XMLHttpRequest.prototype.setRequestHeader = function(k, v) {
  if (String(k).toLowerCase() === 'authorization') window.__auth = v;
  return os.apply(this, arguments);
};
window.__api = async (p, init={}) => {
  const r = await fetch(p, {...init, headers: {Accept: 'application/json', authorization: window.__auth, ...(init.headers||{})}});
  return {status: r.status, body: await r.text()};
};
```

裝好後在站內點一個單元（SPA 換頁不會清掉 hook），`window.__auth` 就有值了。之後所有 API 都透過 `window.__api` 在頁面內呼叫。**不要**把 `window.__auth` 回傳到 javascript_tool 的結果——擴充套件會擋，也不該擋不住。

若是 `fetch` 而非 XHR，改包 `window.fetch` 讀 `init.headers`。

## 資料怎麼帶出瀏覽器

只有剪貼簿可靠。原因：Chrome 對第二次起的程式化下載靜默拒絕；擴充套件會遮蔽含簽名／token／base64 的回傳值；沒有本機檔案系統存取。

```js
// 1. 把結果放到 window.__manifest 後，掛一個 click handler
window.__copyRes = 'pending';
document.addEventListener('click', function h() {
  document.removeEventListener('click', h, true);
  const s = JSON.stringify(window.__manifest);
  navigator.clipboard.writeText(s).then(() => window.__copyRes = 'ok', e => {
    const ta = document.createElement('textarea'); ta.value = s; ta.style.position = 'fixed';
    document.body.appendChild(ta); ta.focus(); ta.select();
    window.__copyRes = 'fallback:' + document.execCommand('copy'); ta.remove();
  });
}, true);
```

接著 `computer.left_click` 點頁面空白處（真實使用者手勢），再讀 `window.__copyRes`。本機用 `LANG=en_US.UTF-8 pbpaste > manifest.json` 接。這會覆蓋使用者的剪貼簿，收尾時提一句。

## 簽名網址時效

| 來源 | 常見時效 | 對策 |
|---|---|---|
| S3 presigned（講義） | 5–15 分鐘 | 簽完立刻下載；下載腳本把講義排第一 |
| CloudFront signed（影片） | 1–2 小時 | 4 路並行，3 MB/s 時 4 GB 約 25 分鐘 |
| 過期回 403 | — | 回頁面重簽該項，腳本會跳過已完成的 |
