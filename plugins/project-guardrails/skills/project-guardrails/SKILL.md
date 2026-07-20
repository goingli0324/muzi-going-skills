---
name: project-guardrails
description: 為專案建立「連動禁區」防護段落。自動分析專案程式碼,找出高扇入模組、資料結構契約、部署設定、對外契約與演算法核心等「改 A 會壞 B」的高風險區域,經使用者確認後寫入該專案的 CLAUDE.md,作為日後所有修改行為的防護依據。MANDATORY TRIGGERS:使用者說「建立連動禁區」「設定 guardrails」「init guardrails」「幫這個專案建立防護」「分析哪些程式碼不能亂動」「哪些模組牽一髮動全身」「建立修改防護段落」「把禁區寫進 CLAUDE.md」,或在新專案開始前要求建立修改安全機制時,都要套用此 skill。適用於 Firebase/PWA、GAS、後端服務等各類專案。SCOPE:本 skill 只做分析與(經確認後的)CLAUDE.md 寫入,不修改任何程式碼。本 skill 同時是 agentic-dev-loop 開發迴圈的「前置」階段：當該編排器在 Step 0 發現專案尚未建立連動禁區時會呼叫本 skill；使用者單獨要求分析禁區時仍直接觸發本 skill。
---

# Project Guardrails(連動禁區建置)

分析專案程式碼,推導出改動風險最高的「連動禁區」,經使用者確認後寫入專案 CLAUDE.md。每個專案執行一次即可;專案架構大改後可重跑更新。

## 執行流程

### Step 1:判斷專案類型

讀取根目錄設定檔(package.json、firebase.json、.firebaserc、appsscript.json、
pom.xml / build.gradle、requirements.txt 等),判斷這是網頁前端、PWA、GAS 專案、
後端服務或混合型。後續檢查項目依類型調整。

### Step 2:推導連動禁區候選清單

逐類檢查,每項都要找到實際證據(檔案:行號),不可僅憑檔名推測:

1. **高扇入模組**:被 3 處以上呼叫的函式/模組/共用元件(用 grep 統計呼叫點)
2. **資料結構契約**:localStorage/IndexedDB 的 key 與 schema、資料庫 schema、
   GAS 專案的 Sheet 欄位結構與 Script Properties、API 的 request/response 格式
3. **部署設定**:.firebaserc、firebase.json、部署指令中的 --account 與 -P 旗標、
   GCP 設定、appsscript.json 權限範圍——此類一律列為禁區
4. **對外契約**:公開 URL 路由、Webhook 端點(如 LINE callback)、
   第三方服務串接點(Gemini API、LINE Messaging API 等)
5. **演算法核心**:計分、分級、判定等一旦改動就讓歷史資料不可比的邏輯
6. **PWA 基礎設施**(若適用):service worker 快取策略、manifest.json

### Step 3:確認後才寫入(硬性規定)

將推導結果整理成草稿,每項包含:模組名稱、實際檔案位置、被依賴方清單、
改動風險一句話。**完整呈現給使用者確認;在使用者明確回覆確認前,
不得寫入任何檔案。**

### Step 4:寫入專案 CLAUDE.md

- 已有 CLAUDE.md:將「## 連動禁區(修改前必讀)」段落附加於文末,
  不覆蓋、不改動任何既有內容;若已有同名段落,先呈現新舊差異讓使用者選擇
- 沒有 CLAUDE.md:建立之,內容為專案一句話簡介 + 連動禁區段落

### Step 5:回報

回報共列入幾項禁區,並明確指出哪幾項信心較低、建議使用者人工複核。
推導不到證據的項目寧可不列,也不要靠猜測充數——禁區寫錯方向比沒寫更危險。
