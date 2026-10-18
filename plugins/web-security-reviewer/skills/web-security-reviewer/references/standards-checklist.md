# 業界標準對照清單

審查時拿來「對號入座」的清單：每個發現要標它對應哪個標準代號，報告最後要有標準涵蓋表（格式見 `report-format.md`）。這份清單不取代各技術棧的 reference，而是告訴你「這條標準在我的技術棧裡要看哪裡、細節去哪份 reference 找」。

## 版本與查證依據（查證日期 2026-10-19）

| 標準 | 版本 | 發布日期 | 官方網址 | 備註 |
|---|---|---|---|---|
| OWASP Top 10 | 2025 | 官方頁未寫日期。二手來源：2025-11 在 OWASP Global AppSec（華府）公布；定稿月份說法不一（2025-11 或 2026-01） | <https://top10.owasp.org/2025>（舊網址 owasp.org/Top10/2025/ 308 轉址至此） | 十條名稱已逐條對過官方頁 |
| OWASP Top 10 for LLM Applications | 2025（v2.0） | 2024-11-18／19（OWASP GenAI 新聞稿與文件日期差一天） | <https://genai.owasp.org/llm-top-10/> | 官方頁未列 2026 版 |
| OWASP ASVS | 5.0.0 | 2025-05-30（GitHub release `v5.0.0_release`） | <https://owasp.org/www-project-application-security-verification-standard/>、<https://github.com/OWASP/ASVS/tree/master/5.0/en> | 截至查證日無 5.0.x 修訂版；引用格式建議帶版本，如 `v5.0.0-6.2.1` |
| CWE Top 25 | 2025 | 官方頁只寫「Page Last Updated: December 15, 2025」，未寫發布日 | <https://cwe.mitre.org/top25/archive/2025/2025_cwe_top25.html> | 2026 年版截至查證日尚未出現 |
| OWASP API Security Top 10 | 2023 | 官方頁未寫日期（頁尾 © 2023） | <https://api-security.owasp.org/> | 官方頁未提新版進行中 |

**未納入但值得知道**：OWASP GenAI 專案在 2025-12 公布「Top 10 for Agentic Applications 2026」（ASI01–ASI10），本次只查到二手來源、沒打開官方頁核對條目，**不當代號使用**。下次更新本檔時再查。

**更新規則**：用到本檔前若距查證日超過半年，先上官方頁確認有沒有新版；版本變了就整份重對，不要只改年份。

---

## 技術棧縮寫

下表「要看什麼」一欄用這些縮寫：**FB** = Firebase（Firestore／Storage rules、Hosting、Functions）｜**GAS** = Google Apps Script Web App｜**CR** = Cloud Run／Express 後端｜**ST** = 靜態站（含打包前端）｜**LINE** = LINE Messaging API webhook。

---

## 一、OWASP Top 10:2025（所有網頁專案都對）

| 代號 | 白話說明 | 在技術棧裡要看什麼 | 細節見 |
|---|---|---|---|
| A01:2025 Broken Access Control | 該擋的人沒擋住：看到或改到別人的資料、越權呼叫管理功能。官方頁把 CWE-918（SSRF）列在這條的對應 CWE 裡 | FB：rules 是否 `allow read, write: if true`、只驗 `request.auth != null` 而不驗擁有者；Storage 路徑可列舉。GAS：`executeAs: USER_DEPLOYING`＋`ANYONE_ANONYMOUS` 時每個操作有沒有自己驗身分；`e.parameter` 能不能指定要讀哪份檔。CR：每支路由都有授權 middleware、ID 從 token 取不從 body 取；伺服器端抓網址有沒有白名單。LINE：只回覆 webhook 帶來的 userId，不讓使用者指定別人 | `security-backend.md`、`security-apps-script.md` |
| A02:2025 Security Misconfiguration | 設定放太寬：預設帳密、除錯模式、CORS `*`、缺安全標頭、雲端資源公開 | FB：Hosting 標頭（CSP、HSTS）、App Check 有沒有開。GAS：`XFrameOptionsMode.ALLOWALL` 的理由是否成立。CR：`cors({origin:'*'})`、`NODE_ENV`、錯誤頁是否吐堆疊。ST：source map 是否上線 | `security-frontend.md`、`data-leakage.md` |
| A03:2025 Software Supply Chain Failures | 第三方套件、CDN、建置管線被汙染或有已知漏洞 | ST／CR／FB Functions：lockfile、`npm audit`、CDN `<script>` 有沒有 SRI 與鎖版本。GAS：外部 Library 的 Script ID 與版本。AI 生成碼：虛構套件名 | `dependency-scanning.md`、`ai-generated-code.md` |
| A04:2025 Cryptographic Failures | 該加密的沒加密、用弱演算法、金鑰管理差 | 全部：HTTP 明文傳輸、自己寫雜湊存密碼、金鑰寫死在程式。LINE：webhook 簽章比對用常數時間比較 | `security-backend.md`、`data-leakage.md` |
| A05:2025 Injection | 使用者輸入被當成程式或查詢執行：SQL、NoSQL、指令、XSS、公式注入 | ST：`innerHTML`、`eval`、`document.write`。GAS：寫進試算表的值以 `= + - @` 開頭（公式注入）、`HtmlService` 用 `<?!= ?>` 不跳脫輸出。CR：字串拼接查詢、`child_process`。LLM 輸出塞進 DOM 也算（另見 LLM05） | `security-frontend.md`、`security-backend.md`、`security-apps-script.md` |
| A06:2025 Insecure Design | 設計上就沒想到濫用情境：沒有速率限制、流程可跳步、信任前端算出來的結果 | 全部：匿名端點有沒有用量上限、報名／投票能不能重送、價格與資格是否在後端重算 | `stress-and-performance.md`、`security-backend.md` |
| A07:2025 Authentication Failures | 身分驗證可被猜、被重放、被繞過 | FB：Auth 是否開了匿名登入卻當成已驗證；自訂 claims 從哪來。GAS：用 `Session.getActiveUser()` 在匿名部署下拿到空字串卻當成通過。CR：JWT 驗簽、過期、登入暴力嘗試限制。LINE：沒驗 `x-line-signature` 等於任何人都能假冒 LINE 平台 | `security-backend.md`、`security-apps-script.md` |
| A08:2025 Software or Data Integrity Failures | 未經驗證就信任資料或更新：不安全的反序列化、未簽章的 webhook、CI 未保護 | LINE／金流 webhook 簽章；FB Functions 的觸發來源；GAS 從 Sheet 讀設定當程式邏輯 | `security-backend.md` |
| A09:2025 Security Logging and Alerting Failures | 出事了沒有紀錄、沒有告警；或 log 反而寫進個資與金鑰 | GAS：`console.*` 進 Cloud Logging，有沒有寫 PII；有沒有異常量告警。CR／FB：Cloud Logging 告警、預算告警。LLM：成本告警（見 LLM10） | `data-leakage.md` |
| A10:2025 Mishandling of Exceptional Conditions | 例外處理不當：錯誤時「放行」(fail open)、把內部錯誤細節回給使用者、資源沒釋放 | 全部：`catch` 裡回傳 `error.message` 或堆疊；限流／驗證壞掉時預設放行；GAS `LockService` 沒在 `finally` 釋放 | `security-backend.md`、`security-apps-script.md` |

## 二、OWASP Top 10 for LLM Applications 2025（專案有呼叫 LLM 才對）

細節、檢查方法與測試輸入全部在 `security-llm-apps.md`，這裡只列對照。

| 代號 | 白話說明 | 在技術棧裡要看什麼 |
|---|---|---|
| LLM01:2025 Prompt Injection | 使用者或外部內容（網頁、檔案、信件、行事曆）裡的文字改變了模型行為 | 使用者輸入、檢索結果、工具回傳是否與指令分開；有沒有任何訪客可控字串被組進 system prompt |
| LLM02:2025 Sensitive Information Disclosure | 模型回覆洩漏個資、金鑰、內部資料 | prompt 或 RAG 資料裡有沒有個資與金鑰；log 是否完整記錄對話 |
| LLM03:2025 Supply Chain | 模型、套件、外掛、第三方 LLM 平台（Dify 等）的供應鏈風險 | SDK 版本、模型來源、平台外掛權限 |
| LLM04:2025 Data and Model Poisoning | 訓練或知識庫資料被汙染 | 誰能改 RAG 來源（Sheet、Drive、知識庫）；同步流程有沒有審核 |
| LLM05:2025 Improper Output Handling | 模型輸出未經處理就被當 HTML、SQL、指令、網址執行 | 回覆用 `innerHTML` 呈現、Markdown 轉 HTML 的跳脫、輸出直接進 `eval`／查詢／工具參數 |
| LLM06:2025 Excessive Agency | 模型拿到的工具、權限、自主程度超過需要 | 工具清單、寫入類工具有沒有人工確認、API 金鑰權限範圍 |
| LLM07:2025 System Prompt Leakage | system prompt 被套出；更大的問題是把金鑰、權限邏輯寫在 prompt 裡 | prompt 裡有沒有金鑰、內部網址、「只有管理員才…」這種靠 prompt 執行的權限 |
| LLM08:2025 Vector and Embedding Weaknesses | 向量庫的存取控制、跨租戶外洩、嵌入資料被反推 | 向量庫是否依使用者過濾、索引裡有沒有不該公開的文件 |
| LLM09:2025 Misinformation | 模型講錯（幻覺）卻被當成官方答案 | 涉及費用、日期、資格的回覆有沒有來源與「以官方公告為準」提示 |
| LLM10:2025 Unbounded Consumption | 無上限的使用量：被刷 token、刷檢索、拖垮服務或帳單 | 身分驗證、速率限制、每日上限、輸入長度、`max_output_tokens`、預算告警 |

## 三、OWASP API Security Top 10:2023（有對外 API 才對：CR、FB Functions、GAS `doGet`/`doPost`、LINE webhook）

| 代號 | 白話說明 | 在技術棧裡要看什麼 | 細節見 |
|---|---|---|---|
| API1:2023 Broken Object Level Authorization | 改網址或參數裡的 ID 就能拿到別人的資料 | CR：`/api/users/:id` 有沒有比對 token 裡的使用者。GAS：`e.parameter.id` 直接拿去讀列。FB：Firestore 路徑 `users/{uid}` 規則有沒有比對 `request.auth.uid` | `security-backend.md` |
| API2:2023 Broken Authentication | API 的身分驗證弱或可繞過 | 同 A07；GAS 匿名端點用「隱藏網址」當密碼 | `security-apps-script.md` |
| API3:2023 Broken Object Property Level Authorization | 回傳了不該給的欄位，或允許改不該改的欄位（mass assignment） | CR：`res.json(user)` 整筆回傳；`Object.assign(doc, req.body)`。FB：rules 沒限制可寫欄位 | `security-backend.md` |
| API4:2023 Unrestricted Resource Consumption | 沒有限流、分頁、大小上限 | 所有端點；LLM 呼叫另見 LLM10 | `stress-and-performance.md` |
| API5:2023 Broken Function Level Authorization | 一般使用者能呼叫管理功能 | GAS：所有 `google.script.run` 可呼叫的全域函式都等於公開 API。CR：admin 路由只靠前端隱藏 | `security-apps-script.md` |
| API6:2023 Unrestricted Access to Sensitive Business Flows | 業務流程被自動化濫用（搶名額、灌表單、刷 AI 額度） | 報名、投票、AI 客服：有沒有每人／每 IP／全站上限 | `stress-and-performance.md` |
| API7:2023 Server Side Request Forgery | 伺服器替使用者去抓任意網址 | CR／GAS：`fetch(req.body.url)`、`UrlFetchApp.fetch(e.parameter.url)` | `security-backend.md` |
| API8:2023 Security Misconfiguration | 同 A02，API 版 | CORS、錯誤回應、HTTP 方法 | `security-backend.md` |
| API9:2023 Improper Inventory Management | 舊版、測試版端點還活著 | GAS：舊部署版本仍可存取；CR：舊 revision、測試 service 沒關 | `security-apps-script.md` |
| API10:2023 Unsafe Consumption of APIs | 盲目信任第三方 API 回傳（含 LLM API） | 第三方回傳值直接進 DOM／資料庫；逾時與失敗降級 | `security-backend.md` |

## 四、CWE Top 25:2025（逐條對發現標 CWE 編號用）

記憶體類（CWE-787、416、125、120、476、121、122）在 JavaScript／GAS 專案通常**不適用**，涵蓋表標「不適用：受管記憶體語言」即可。

| 名次 | CWE | 名稱 | 常見落點 | 對應 OWASP |
|---|---|---|---|---|
| 1 | CWE-79 | Cross-site Scripting | `innerHTML`、GAS `<?!= ?>`、LLM 回覆轉 HTML | A05 |
| 2 | CWE-89 | SQL Injection | CR 字串拼接查詢 | A05 |
| 3 | CWE-352 | CSRF | Cookie 驗證的 CR 表單；GAS `doPost` 改狀態 | A01 |
| 4 | CWE-862 | Missing Authorization | GAS 公開函式、Firestore rules 只驗登入 | A01 |
| 5 | CWE-787 | Out-of-bounds Write | 記憶體類 | — |
| 6 | CWE-22 | Path Traversal | CR 讀檔、Storage 路徑由使用者組 | A01 |
| 7 | CWE-416 | Use After Free | 記憶體類 | — |
| 8 | CWE-125 | Out-of-bounds Read | 記憶體類 | — |
| 9 | CWE-78 | OS Command Injection | CR `child_process.exec` | A05 |
| 10 | CWE-94 | Code Injection | `eval`、`new Function`、LLM 輸出被執行 | A05／LLM05 |
| 11 | CWE-120 | Classic Buffer Overflow | 記憶體類 | — |
| 12 | CWE-434 | Unrestricted Upload of File with Dangerous Type | Storage 上傳、GAS 存 Drive | A06 |
| 13 | CWE-476 | NULL Pointer Dereference | 記憶體類 | — |
| 14 | CWE-121 | Stack-based Buffer Overflow | 記憶體類 | — |
| 15 | CWE-502 | Deserialization of Untrusted Data | CR 用不安全的反序列化套件 | A08 |
| 16 | CWE-122 | Heap-based Buffer Overflow | 記憶體類 | — |
| 17 | CWE-863 | Incorrect Authorization | 授權邏輯寫錯（比錯欄位、比對大小寫） | A01 |
| 18 | CWE-20 | Improper Input Validation | 所有入口 | A05／A06 |
| 19 | CWE-284 | Improper Access Control | 雲端資源公開、rules 過寬 | A01 |
| 20 | CWE-200 | Exposure of Sensitive Information | 錯誤訊息、log、bundle、LLM 回覆 | A01／LLM02 |
| 21 | CWE-306 | Missing Authentication for Critical Function | 匿名可呼叫的寫入／付費端點 | A07 |
| 22 | CWE-918 | SSRF | 伺服器端抓使用者給的網址 | A01 |
| 23 | CWE-77 | Command Injection | 指令組字串 | A05 |
| 24 | CWE-639 | Authorization Bypass Through User-Controlled Key | 用 body／query 裡的 ID 決定讀誰的資料 | A01／API1 |
| 25 | CWE-770 | Allocation of Resources Without Limits or Throttling | 無限流、無分頁、LLM 無上限 | A06／LLM10 |

## 五、OWASP ASVS 5.0.0（要做「比較完整的驗證」時挑章節用）

ASVS 是逐條可驗證的需求清單，條目很多，**不要整本跑**。依專案挑下列章節，報告裡引用時寫成 `ASVS v5.0.0-章.節.條`（例如 `v5.0.0-6.2.1`）；沒有逐條核對就只寫章，不要編條號。

| 章 | 名稱 | 什麼專案要挑 |
|---|---|---|
| V1 | Encoding and Sanitization | 所有有輸出到 HTML／試算表／查詢的專案 |
| V2 | Validation and Business Logic | 報名、表單、配額、AI 用量閘 |
| V3 | Web Frontend Security | ST、FB Hosting、GAS HtmlService |
| V4 | API and Web Service | CR、FB Functions、GAS `doPost`、LINE webhook |
| V5 | File Handling | 有上傳功能 |
| V6 | Authentication | 有登入 |
| V7 | Session Management | CR 自管 session |
| V8 | Authorization | 有角色或多使用者資料 |
| V9 | Self-contained Tokens | 用 JWT／Firebase ID token |
| V10 | OAuth and OIDC | Google 登入、LINE Login |
| V11 | Cryptography | 自己做加密或雜湊 |
| V12 | Secure Communication | 一律（HTTPS、TLS） |
| V13 | Configuration | 一律（祕密管理、部署設定） |
| V14 | Data Protection | 含個資的專案 |
| V15 | Secure Coding and Architecture | 一律 |
| V16 | Security Logging and Error Handling | 一律 |
| V17 | WebRTC | 有即時影音才挑 |

---

## 依專案類型挑條目（第 1 步用）

| 專案類型 | 必對 | 視情況加對 |
|---|---|---|
| 純靜態站（無後端） | A02、A03、A05、A09；CWE-79、CWE-200 | 有表單寄送就加 A06、API4 |
| Firebase（Hosting＋Firestore／Storage） | A01、A02、A05、A07；API1、API3；CWE-862、CWE-284、CWE-639 | 有 Functions 加 API 全套；有上傳加 CWE-434、ASVS V5 |
| GAS Web App | A01、A05、A06、A07、A10；API5、API9；CWE-862、CWE-306 | 寫試算表就特別看公式注入（A05）；含個資加 ASVS V14 |
| Cloud Run／Express API | A01–A10 全套；API 全套 | ASVS V4、V6、V8 |
| LINE webhook | A07、A08（簽章）、A06；API4、API6 | 接 LLM 就加 LLM 全套 |
| 有呼叫 LLM（Anthropic、Gemini、OpenAI SDK、Dify 等） | 上面對應類型 ＋ LLM01–LLM10 全部；必讀 `security-llm-apps.md` | 有 RAG 加 LLM08；有工具呼叫重看 LLM06 |
