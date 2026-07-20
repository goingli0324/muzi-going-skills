# 相依套件漏洞掃描（SCA）

## 定位
- 這類工具掃的是「你裝的第三方套件」有沒有**已知** CVE，不是你自己寫的邏輯漏洞。和本 skill 其他步驟（審查使用者自己的碼）是互補的兩件事，不要混為一談。
- 一律歸為 🔧（需你操作）：skill 讀不到使用者的 lockfile、也不在其環境執行，只能教使用者怎麼跑、怎麼讀結果。**不要把任何掃描結果寫成定論**——模型知識有時間截點，列出的 CVE 編號可能過時。

## 第一件事：判斷「這個專案到底用不用得上」
沒有 lockfile，這兩個工具都使不上力。先確認專案型態：

| 專案型態 | 適用工具 | 說明 |
|---|---|---|
| 純 Google Apps Script（線上編輯器 / `appsscript.json`，無 npm） | ❌ 大多不適用 | GAS 跑在 Google V8，不吃 npm 套件樹。相依風險改看：透過 Script ID 加入的外部函式庫、`UrlFetchApp` 打的第三方 API、OAuth scope 是否過寬。 |
| GAS + clasp + Node 建置（有 `package.json` / `package-lock.json`） | ✅ `npm audit` / `osv-scanner` | 此時才有真正的 npm 相依樹可掃。 |
| 前端有打包（Vite / webpack / 用 npm 安裝套件） | ✅ `npm audit` / `osv-scanner` | |
| 前端純 CDN `<script>`（無 lockfile） | ⚠️ 兩者都掃不到 | 改用 SRI（Subresource Integrity）、鎖死版本、注意 CDN 供應鏈。 |
| 後端 Node | ✅ `npm audit`（首選，零安裝）／`osv-scanner` | |
| 後端 Python | ✅ `pip-audit`／`osv-scanner` | |
| 多語言 / monorepo / 容器映像 / SBOM | ✅ `osv-scanner` | |

## 兩者怎麼選
- **`npm audit`**：Node 內建，零安裝零設定，只認 npm 生態，比對 GitHub Advisory Database。JS / Node 專案的最低摩擦起點。`npm audit fix` 會自動升可安全升級的；`--omit=dev` 只看 production 相依。
- **`osv-scanner`**（Google 維護，需另裝）：跨生態（npm、PyPI、Go、Maven、Cargo…），比對 OSV.dev 資料庫，可掃 lockfile、SBOM、容器映像；因為用生態專屬比對（而非 NVD 的 CPE 比對），誤報率通常較低。`osv-scanner fix`（guided remediation）目前主要支援 npm / Maven。
- **結果可能不同**：兩者資料庫與比對方式不同，曾有同一漏洞一邊報一邊不報的情況，不是誰一定對。多語言或要進 CI → `osv-scanner`；單純 Node 想快 → `npm audit`；要保險可兩個都跑當交叉驗證。

## 怎麼讀結果、怎麼處置
- **嚴重度看實際用法**：別只照抄工具給的標籤。一個只在伺服器端渲染才觸發的漏洞，對純前端 build 可能無實際影響。判斷「這個漏洞在你的用法下會不會真的被觸發」。
- **能自動修的先修**：`npm audit fix` / `osv-scanner fix` 能解的歸 ✅。
- **要 major 升級的**：標為 ⚠️（可能 breaking），說明取捨，保留決定權。
- **升不動的**（上游未修）：評估能否移除該套件、換套件、或用設定迴避；列 🔧。
- **transitive（間接相依）漏洞**：通常要靠升級直接相依、或 npm `overrides` / yarn `resolutions` 處理，提醒這可能牽動相容性。

## 進 CI（可選，⚠️/🔧）
- 可在 CI 加一關（PR 時跑 `osv-scanner` / `npm audit`），但要設 fail 門檻（例如只擋 high / critical），否則 noise 太多會被整支忽略。是否阻斷部署、門檻設多高，由使用者決定。

## 限制（要對使用者講清楚）
- 只抓「已知且已收錄」的漏洞——zero-day、未揭露、或使用者自己邏輯的漏洞都抓不到（後者是本 skill 其他步驟的工作）。
- 結果有時效性，**以使用者實跑當下的輸出為準**，不要採信模型憑記憶列的 CVE 編號。
- 「audit 乾淨」≠ 沒有供應鏈風險。惡意套件、typosquatting、安裝期惡意行為不在一般 CVE 掃描範圍內（那是 install-time 行為分析工具的領域，如 Socket）。
