# 部署前安全檢查清單（多帳號 / 多專案）

最高頻、代價最大的開發事故不是寫錯邏輯，是**部署到錯的帳號或錯的專案**。若你有多個 Firebase CLI 帳號與專案，這份清單是防呆。

> 與 project-guardrails 的關係:部署設定（`.firebaserc`、`firebase.json`、`--account`/`-P` 旗標、`appsscript.json` 權限）通常已被 project-guardrails 列為 CLAUDE.md 連動禁區。那是**靜態警告**（規劃時讀到「這些別亂改」）;這份清單是**動作當下的核對**（按下部署前確認沒部署錯地方）。兩者互補，不重複。

> 本 skill **不替使用者執行部署**。以下是使用者親自操作前要核對的清單;skill 的角色是把清單攤開、把目標環境寫進 plan.md、並在任何看起來會誤部署時喊停。

## 放行前提（在帳號核對之前，這些要先成立）

- [ ] Verify 雙閘該走的都走了，無未解 P0 / Critical / High
- [ ] **smoke 閘**:有 `test:smoke` 的專案已跑過（可用 `/predeploy` 自動偵測串接）；Build 出口那份 smoke 清單已**人工逐項驗過**——照全域 CLAUDE.md §三，未經人工驗證視同未過
- [ ] 修正過程未為了過測試而硬改 `src/`（全域 §四 鐵則）

## 核心防呆原則

1. **部署目標寫死，不靠記憶。** 在部署腳本與 `CLAUDE.md` 裡硬寫 `--project` 與帳號旗標，不依賴「當前作用中的帳號剛好是對的」。這是已驗證有效的做法。
2. **部署前出聲確認。** 任何 🟡/🔴 部署，先把「帳號 + 專案 ID + 環境（prod/staging）」念出來核對，再按下去。
3. **工作與個人帳號分視窗。** 平行作業時不同帳號用不同終端視窗，降低在錯的 session 打 deploy 的機率。

## Firebase Hosting / Firestore

- [ ] `firebase projects:list` 確認當前帳號能看到目標專案
- [ ] 部署指令帶明確旗標:`firebase deploy --project <PROJECT_ID> --only hosting`（或對應的 only 範圍）
- [ ] 確認 `--only` 範圍正確:只改 hosting 卻帶上 `firestore` 規則會誤覆蓋
- [ ] 動過 security rules → 必須已過 Verify（web-security-reviewer）
- [ ] PWA:service worker / 快取版本號已更新，舊使用者不會卡舊版

## Google Apps Script（clasp）

- [ ] `clasp status` 確認連到正確的 script id
- [ ] `.clasp.json` 的 `scriptId` 與目標一致（多專案最容易在這裡出錯）
- [ ] Web App 部署設定:執行身分、存取權限符合計畫（對外公開的要特別確認）
- [ ] 讀寫的 Sheet/Drive 是否含個資 → 含則此次部署屬 🔴，須先過 Verify
- [ ] 建立**新版本**部署而非覆蓋既有 head，保留回滾點

## Cloud Run / GCP

- [ ] `gcloud config get-value project` 確認專案;必要時 `gcloud config set project <ID>`
- [ ] 環境變數與 Secret Manager 條目對齊計畫，**真實祕密值由使用者寫入，不經 skill**
- [ ] 有 DB migration → 單獨確認、先備份、可回滾
- [ ] 先部署到 staging/非正式環境驗證，再上 prod
- [ ] 記下這次部署的 image tag / revision，方便出事回滾

## 出事的回滾預設

- Firebase Hosting:`firebase hosting:rollback` 或重新部署上一個已知良好版本
- GAS:切回前一個部署版本
- Cloud Run:`gcloud run services update-traffic` 切回上一個 revision

回滾路徑要在部署**之前**就知道。不知道怎麼回滾，就還沒準備好部署。
