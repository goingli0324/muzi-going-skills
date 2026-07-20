# plan.md 結構化模板

`plan.md` 是整條迴圈的單一事實來源。它要能讓「明天的你」或「一個全新的 session」只讀這份檔案就接得下去。

## 通用骨架

```markdown
# Plan: <主題> (<YYYY-MM-DD>)

## 風險級別
🟢 / 🟡 / 🔴  ← 決定授權與驗證強度（見 SKILL.md 分流表）

## 目標部署環境
- 平台: Firebase Hosting / Cloud Run / GAS / 其他
- 帳號: <Firebase CLI 帳號 email>      ← 三帳號情境必填，避免誤部署
- 專案 ID: <firebase project id / gcp project / gas script id>

## 問題陳述
（要解什麼、為什麼現在解、不解的後果）

## 研究結論（Research 步驟產出）
- 決策依據 1（附來源）
- 決策依據 2
- 選型結論與被否決的選項及理由

## 採用方法與理由
（怎麼做、為什麼這樣做而不是別的方式）

## 要動的檔案
- path/to/file_a — 改什麼
- path/to/file_b — 新增什麼

## 要遵循的既有模式
（這個 repo 已有的命名/結構/慣例，新碼要對齊的對象）

## 連動禁區檢查（對照 CLAUDE.md）
- 這次要動的檔案有沒有踩到 project-guardrails 寫進 CLAUDE.md 的連動禁區?
- 若有:列出受影響的「被依賴方」，並在下方驗收標準補上「驗證這些下游沒被弄壞」
- 若無:註明「已對照禁區，無踩雷」

## 驗收標準（怎樣算做完）
- [ ] 標準 1（可客觀檢查）
- [ ] 標準 2
- [ ] `test:smoke` 通過（PWA/前端）或手動 smoke 清單逐項驗過（GAS）
- [ ] **照全域 §二.7 產出兩份清單**:影響範圍清單 + Smoke test 清單
- [ ] 影響範圍若 >3 檔，已照全域 §二.3 先向使用者回報並確認

## 本輪 Verify 走哪幾道閘
- 閘 A 安全（web-security-reviewer）: 走 / 不走 — 理由
- 閘 B UI/UX（ui-ux-deploy-reviewer）: 走 / 不走 — 有前端介面才走
- 🔴 repo → 閘 A 一律「走，且未過不部署」

## 風險與取捨
（這個方案的已知弱點、被犧牲掉的東西）
```

## 三種變體的補充欄位

### Firebase Hosting / PWA（如 my-learning-pwa）
- **資料邊界**:這次改動會不會新增「儲存/顯示可識別學習者資料」的路徑?若會 → 升 🔴 並重評。
- **離線/快取行為**:PWA 的 service worker 是否需要更新版本號?舊快取會不會卡住使用者?
- **Firestore/Storage 規則**:有沒有動到 security rules?動了就一定要進 Verify。

### Google Apps Script（如 CLC 各系統）
- **執行身分**:`doGet`/`doPost` 以誰的身分執行?Web App 部署設定（執行者、存取權）寫進計畫。
- **無本地測試框架**:驗收標準改成「手動驗證清單」+「clasp push 前自檢」。
- **配額與執行時間**:有沒有可能踩到 Apps Script 6 分鐘執行上限或每日配額?
- **知識庫/試算表**:讀寫的 Sheet 是否含個資?含 → 🔴。

### Cloud Run（如 校務管理系統）
- **環境變數與祕密**:用了哪些 Secret Manager 條目?計畫只記「用到哪些」，**不寫真實值**。
- **Cloud SQL 連線**:連線方式、是否有 migration?migration 要單獨列為高風險步驟。
- **Scheduler/觸發器**:有沒有改到排程?改了要記下舊行為以便回滾。

## 寫計畫的紀律

- 計畫存進該 repo 的 `plans/` 或 `docs/plans/`，檔名:`YYYY-MM-DD-<主題>.md`。
- 實作中發現計畫有誤 → **先改計畫再改碼**，不要讓兩者脫鉤。
- 一份計畫值得改三輪。研究薄、驗收標準模糊的計畫，會在實作階段加倍還債。
