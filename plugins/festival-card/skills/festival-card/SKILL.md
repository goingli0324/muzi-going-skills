---
name: festival-card
description: 節慶祝賀卡片產生器——你的主角配一隻 Q 版動物，3D 軟膠公仔質感的節慶場景，卡上疊繁中＋英文祝賀詞。一次出 4 張直式候選讓使用者挑，挑中的再延伸成正方形與橫式（同一份角色像素，不會變形）。內建 37 個台灣節日與節氣的意涵、場景與日期計算。當使用者說「我要○○節的祝賀卡片」「做一張○○的賀卡」「節慶卡片」，或第一次要設定賀卡主角時觸發。
---

# 節慶祝賀卡片

## 位置

- **skill 資料夾**（本檔所在處，下稱 `SKILL_DIR`）：程式與範本。plugin 更新時會整個被覆蓋，**不要把使用者的東西放這裡**。
- **工作資料夾**（下稱 `WORK`，預設 `~/festival-cards`，使用者指定別處就用那裡）：角色設定、參考圖、節慶表、企劃、成品、字型、金鑰。
- 每個指令都在 `WORK` 裡跑，並帶上 `FESTIVAL_CARD_HOME="$WORK"`。

```bash
export FESTIVAL_CARD_HOME="$HOME/festival-cards"; cd "$FESTIVAL_CARD_HOME"
```

## 第一次使用：設定（`WORK/character.json` 不存在時先做這段）

一項一項做、做完一項確認一項，不要一次全丟給使用者。

1. **環境**：確認有 `node`（18 以上）與 `uv`。缺的請使用者安裝（uv：`curl -LsSf https://astral.sh/uv/install.sh | sh`）。
2. **工作資料夾**：
   ```bash
   mkdir -p "$WORK"/{figures,anchors,fonts,plans,output}
   cp "$SKILL_DIR/templates/festivals.json" "$WORK/"
   cp "$SKILL_DIR/templates/character.example.json" "$WORK/character.json"
   ```
3. **套件**：`cd "$SKILL_DIR" && npm install`（只裝 `@google/genai`）。
4. **Gemini 金鑰**：請使用者**自己**建立 `$WORK/.env`，內容一行 `GEMINI_API_KEY=...`（到 https://aistudio.google.com/apikey 申請，生圖是付費功能）。**不要請使用者把金鑰貼進對話。**確認：`ls -l "$WORK/.env"` 存在即可，不要印出內容。
5. **字型**：預設中文霞鶩文楷 TC Bold、英文 Fraunces（兩者都是 SIL OFL，可商用）。請使用者下載放進 `$WORK/fonts/`：
   - 霞鶩文楷 TC：https://github.com/lxgw/LxgwWenkaiTC/releases 的 `LXGWWenKaiTC-Bold.ttf`
   - Fraunces：https://fonts.google.com/specimen/Fraunces 的 `Fraunces_72pt_Soft-SemiBoldItalic.ttf`、`Fraunces_72pt_Soft-Regular.ttf`
   想用別的字型就改 `character.json` 的 `fonts`（檔名或絕對路徑）。
6. **主角**：照 `SKILL_DIR/docs/主角定版.md` 生 4 張候選讓使用者挑，存成 `figures/main.png`，填好 `character.json` 的 `protagonist`。
7. **動物**：問使用者要哪幾隻（1–4 隻以上皆可，4 隻最好，每張候選換一隻）。照 `SKILL_DIR/docs/動物錨點提示詞範本.md` 逐隻生錨點、對照實拍照片驗收，填進 `character.json` 的 `animals`。
8. **署名**（可省略）：`signature.image` 放簽名圖路徑（透明底 PNG），`signature.wordmark` 放名字；不要就設成 `null`。

## 產卡片

1. **查節慶**：讀 `WORK/festivals.json`。表裡沒有就補一筆（`moon`／`meaning`／`motifs`／`palette`，必要時 `tone`），補完告訴使用者。含月亮的節慶要核對當天農曆月相：
   ```bash
   uv run -q --with lunardate python -c "from lunardate import LunarDate; print(LunarDate.from_solar_date(2026,10,10))"
   ```
2. **寫企劃** `WORK/plans/<節慶>_<日期>.json`：
   ```json
   {"festival": "中秋", "festival_en": "Mid-Autumn Festival in Taiwan", "date": "2026-09-25",
    "cards": [{"animal": "<character.json 的動物代號>", "scene": "...", "figure_action": "...", "expression": "...",
               "animal_action": "...", "zh": "月圓人團圓", "en": "...", "motifs": "（可省略）"}]}
   ```
   - 剛好 4 張；四張的**場景、動作、表情、祝賀詞語氣**都要拉開（溫馨／莊重／活潑／簡短各一種）
   - 動作用整隻手臂的大動作；**不要寫 OK、比數字這類手指動作**（會生錯）
   - 中文祝賀詞 4–12 字，斷行用 `|`；英文自然口語，不逐字翻譯
   - 節慶元素預設套到每一張；某張不該出現（莊重場景不要煙火）就在那張寫 `motifs` 覆寫——只在 scene 寫「不要」壓不過
   - 語意不同 ≠ 畫面不同：寫動作時想「剪影長什麼樣」
3. **生 4 張直式候選**（約 2 分鐘，平行）：
   ```bash
   uv run -q --with pillow python "$SKILL_DIR/scripts/cards.py" draft plans/<檔>.json
   ```
4. **驗收後才給使用者看**：讀 `output/<節慶>_<日期>/sheet.jpg`，再**放大裁臉**跟 `figures/` 的主角原圖並排（縮圖會騙人）。檢查：字壓到頭？主角特徵跑掉？動物花色對？冒出文字、假漢字、兩個角色？月相對？有問題就刪掉 `output/<節慶>_<日期>/raw/<n>_portrait.png` 重跑同一個 draft 指令（只補缺的）。
5. 把 `sheet.jpg` 給使用者看，請他挑編號。
6. **延伸**成正方形與橫式（只要一種就在最後加 `square` 或 `landscape`）：
   ```bash
   uv run -q --with pillow python "$SKILL_DIR/scripts/cards.py" extend output/<節慶>_<日期> <編號>
   ```
   延伸是把直式原圖原封不動放上新畫布、模型只補兩側，所以角色不會變形。驗收：補出來的場景是清楚的（不是一片模糊）、看不出接縫、字不壓頭。
7. **只改祝賀詞**：改 `output/<節慶>_<日期>/plan.json`，跑 `cards.py compose output/<節慶>_<日期>`，不重新生圖。

每次生圖都會在圖旁存一份 `<圖檔名>.prompt.txt`（實際送出的提示詞與參考圖）。

## 選配：提前 3 天自動產

`scripts/festival_dates.py` 會算 37 個節慶的國曆日期（節氣用天文計算、農曆節日換算）：

```bash
uv run -q --with ephem --with lunardate python "$SKILL_DIR/scripts/festival_dates.py" due --days 3
# 輸出「沒有節慶 YYYY-MM-DD」或「YYYY-MM-DD 名稱」；其他輸出一律當成失敗，不可當成沒節慶
uv run -q --with ephem --with lunardate python "$SKILL_DIR/scripts/festival_dates.py" list 2027
```

在 Claude 桌面 app 建一個每天早上的排程，指示寫：跑上面的 `due`、有節慶就照「產卡片」做到第 5 步並推播、使用者回編號再延伸。

## 鐵則

- **AI 不寫中文**：提示詞一律禁字，祝賀詞由程式疊上去（模型寫中文會出現假字）
- **身分鎖不要寫 same face**：寫「same facial features and proportions」，否則表情會被鎖死
- 每張開獨立的生圖 session（程式已處理），共用 session 會累積色偏
- **不要畫國旗**：模型會畫錯（白底、圖案糊掉），國慶用素色紅白藍與煙火
- 金鑰只放 `WORK/.env`，不進對話、不進任何 git
