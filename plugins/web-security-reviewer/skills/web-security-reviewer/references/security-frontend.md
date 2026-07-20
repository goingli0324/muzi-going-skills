# 前端（HTML / CSS / JS）安全檢查清單

前端的鐵則：**送到瀏覽器的一切都是公開的，使用者完全可控**。任何「靠前端擋住」的安全機制都只是 UX，不是安全。逐項對照。

## 1. XSS（跨站腳本，前端最常見的高風險項）

把不可信資料放進 DOM 而沒轉義，攻擊者就能在使用者瀏覽器執行任意 JS（竊取 cookie/session、偽造操作）。

**危險的 sink（輸出點）**：
- `element.innerHTML` / `outerHTML` / `insertAdjacentHTML`
- `document.write`
- `eval()`、`new Function()`、`setTimeout("字串")`、`setInterval("字串")`
- jQuery `.html()`、框架裡的 `dangerouslySetInnerHTML` / `v-html`

**不可信的來源（source）**：URL 參數、`location.hash`、`location.search`、`document.referrer`、`postMessage` 收到的資料、`localStorage`、後端回傳的內容、使用者輸入。

**修補方向**：
- 顯示文字用 `textContent` / `innerText`，不要用 `innerHTML`。
- 一定要塞 HTML，先用 `DOMPurify.sanitize()` 過濾。
- 設定 Content-Security-Policy（CSP）作為第二道防線。

```javascript
// 危險
el.innerHTML = userInput;
// 安全（純文字）
el.textContent = userInput;
// 必須是 HTML 時
el.innerHTML = DOMPurify.sanitize(userInput);
```

## 2. 客戶端不該藏祕密

API key、token、密碼、商業邏輯放在前端 JS = 公開。檢查：

- 硬寫的金鑰／token（含 minified bundle）。
- 「隱藏」的管理員功能只靠前端不顯示按鈕——後端沒擋就形同虛設。
- 修補：機密移到後端；前端只能拿「受限、可公開」的金鑰（例如有 referrer/網域限制的 key）。

## 3. 敏感資料存放

- `localStorage` / `sessionStorage` 可被同頁的 JS（含 XSS 注入的）讀取——不要放 token、個資。
- session/驗證憑證優先用後端設定的 cookie，並帶 `HttpOnly`、`Secure`、`SameSite`。

## 4. postMessage

- 監聽 `message` 事件時**一定要檢查 `event.origin`**，否則任何網站都能傳訊息進來。
- 發送時指定明確 `targetOrigin`，不要用 `"*"` 傳敏感資料。

## 5. 第三方腳本與供應鏈

- 從 CDN 載入的 `<script>` / `<link>` 應加 Subresource Integrity（`integrity` ＋ `crossorigin`），避免 CDN 被竄改後植入惡意碼。
- 審視第三方分析／追蹤腳本是否會讀到表單裡的敏感欄位。

## 6. Clickjacking

- 缺少防護時，網站可被嵌進 iframe 誘導點擊。
- 後端送 `X-Frame-Options: DENY` 或 CSP `frame-ancestors 'none'`。

## 7. 表單與 CSRF

- 前端驗證只是體驗，**後端必須重做驗證**。
- 會改變狀態的請求要有 CSRF 防護（token 或 `SameSite` cookie）。

## 8. 開放轉址（Open Redirect）

- 用 URL 參數決定要跳轉的網址（`location.href = params.next`）會被導去釣魚站。
- 用允許清單（allowlist）或只允許相對路徑。

## 9. 混合內容與 HTTPS

- HTTPS 頁面載入 `http://` 資源（mixed content）會被攔截或降級。全站走 HTTPS。

## 10. 框架特有

- React：避免 `dangerouslySetInnerHTML`；URL 來源（`href={userInput}`）注意 `javascript:` 協定注入。
- Vue：`v-html` 等同 innerHTML，謹慎使用。
- prototype pollution：合併不可信物件（`Object.assign` / 深拷貝 lodash.merge）時，惡意 `__proto__` 可能污染原型鏈。
