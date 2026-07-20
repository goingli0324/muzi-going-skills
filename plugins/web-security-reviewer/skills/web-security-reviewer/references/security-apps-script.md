# Google Apps Script 安全檢查清單

Apps Script 的風險和一般網站不太一樣，最常被忽略的是「部署設定」和「以誰的身分執行」——這兩個錯了，程式碼寫得再乾淨都沒用。逐項對照。

## 1. 部署設定（最高優先，常被忽略）

Web App 部署時有兩個關鍵設定：

- **Execute as（以誰的身分執行）**：`Me（我）` vs `User accessing the web app（存取者本人）`
- **Who has access（誰能存取）**：`Only myself` / `Anyone with a Google account` / `Anyone`

**危險組合**：`Execute as Me` ＋ `Anyone`／`Anyone with a Google account`。這代表任何人觸發你的 web app，程式碼都是用**你的權限**跑——存取你的 Drive、Sheets、Gmail。等於把你的帳號權限借給陌生人。

- 檢查 `appsscript.json` 的 `webapp.executeAs` 與 `webapp.access`。
- 內部工具優先 `executeAs: USER_ACCESSING` 或 `access: DOMAIN`（限組織內）。
- 若必須 `Execute as Me ＋ Anyone`，那 `doGet`/`doPost` 裡**每一個操作前都要自己做授權判斷**，且絕不能讓存取者控制要讀寫哪份檔案。

## 2. doGet / doPost 是公開端點

部署成 `Anyone` 後，`doGet(e)` / `doPost(e)` 就是對外 API。`e.parameter`、`e.parameters`、`e.postData.contents` 全部是**不可信輸入**。

- 一律驗證型別、長度、範圍、必填。
- 不要直接拿 `e.parameter.sheetId` / `e.parameter.file` 去開檔案（等同 IDOR／路徑操控——使用者可指定不屬於他的資源）。
- 對寫入操作加上自己的驗證 token 或登入判斷（`Session.getActiveUser()` 只在 `Execute as User accessing` 時有意義）。

## 3. Sheet 公式注入（CSV / Formula Injection）

把使用者輸入直接寫進儲存格，若內容以 `=`、`+`、`-`、`@` 開頭，會被當公式執行（可能外洩資料或誘導點擊）。

- 寫入前檢查首字元，必要時前置單引號 `'` 或清掉危險前綴。
- 諮輔單這類「使用者填表 → 寫入 Sheet」的流程要特別檢查這一點。

```javascript
function sanitizeForCell(v) {
  const s = String(v);
  return /^[=+\-@\t\r]/.test(s) ? "'" + s : s;
}
```

## 4. 機密不要硬寫在 .gs

API key、token、密碼不要寫死在程式碼。

- 用 `PropertiesService.getScriptProperties()` 或 `getUserProperties()`。
- **注意**：Script Properties 對「有編輯權的協作者」可見，不是真正的祕密保險箱。真正高敏感的金鑰，應放在後端服務，Apps Script 只透過受限介面呼叫。
- 檢查是否有金鑰被 commit 進版本歷史；若洩漏要輪替（rotate）。

## 5. OAuth 範圍最小化

`appsscript.json` 的 `oauthScopes` 決定這支腳本能碰多少東西。範圍越大，出事時的爆炸半徑越大。

- 只宣告真正用到的範圍（例如只需讀某 Sheet 就別要 full Drive）。
- 審查是否有「為了省事」而宣告的過廣範圍。

## 6. 併發與競態（對表單簽核特別重要）

多人同時寫同一份 Sheet 會有 race condition：重複提交、覆蓋彼此的更新、號碼跳號。

- 對「讀-改-寫」的關鍵區段用 `LockService`（`getScriptLock()` / `getDocumentLock()`），搭配 `waitLock` 與 `try/finally releaseLock`。
- 諮輔單的「簽核 / 編號」流程若沒上鎖，高併發下會出現重複或遺失。

```javascript
function withLock(fn) {
  const lock = LockService.getScriptLock();
  lock.waitLock(10000); // 最多等 10 秒
  try { return fn(); } finally { lock.releaseLock(); }
}
```

## 7. HtmlService 的 XSS

- 用 `HtmlService.createTemplateFromFile` 時，`<?= value ?>` 會自動轉義（安全），`<?!= value ?>` **不轉義**（危險）。把使用者資料放進 `<?!= ?>` 要特別標記。
- 不要用字串拼接組 HTML 再塞使用者輸入。
- 確認在 IFRAME sandbox 模式（現為預設）。

## 8. 不要在程式碼裡放寬權限

- 留意 `setSharing(ANYONE, EDIT)`、`addEditor(不可信的 email)`、`DriveApp` 把檔案設為公開——這會把檔案暴露給非預期對象。
- （提醒：實際變更分享設定請由使用者自己在介面操作；skill 只負責「標出」程式碼裡的風險寫法。）

## 9. Log 與個資

- `Logger.log` / `console.log` 會進 Cloud Logging，可能把 PII 留在 log 裡。寫入前遮蔽（mask）敏感欄位。

## 10. 觸發器（Triggers）

- 時間觸發、`onEdit` 等是以建立者身分執行；可安裝觸發器（installable trigger）以建立它的人的權限跑。確認觸發器不會在無人監督下用高權限做敏感操作。

## 配額與執行限制（壓力／效能相關，細節見 stress-and-performance.md）

- 單次執行時間上限（一般帳號約 6 分鐘）。
- 迴圈內反覆呼叫 `SpreadsheetApp`（一格一格讀寫）非常慢且易超時——改用 `getValues()` / `setValues()` 批次處理。
- URL Fetch、寄信等各有每日配額。
