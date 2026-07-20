---
name: ai-roleplay-practice
description: Sets up an interactive AI roleplay so the user can rehearse a difficult conversation or scenario — any persona, any context — with structured feedback at the end. Use this whenever the user wants to practice, rehearse, or prepare for a conversation by having AI play a specific role (a difficult student, a skeptical parent, a colleague pushing back, a dissertation committee member, an interviewer, a negotiation counterpart, or any other identity the user names), says things like "讓AI扮演...", "陪我練習...", "模擬一下...情境", or wants a safe, repeatable space to rehearse before a real high-stakes interaction. The persona is never fixed to one category — always let the user define who AI plays, and offer example personas only as starting suggestions.
---

# AI 角色扮演練習夥伴 (AI Roleplay Practice)

## 核心理念

在 AI 面前可以犯錯、可以無限次重來,不會有真實後果,直到掌握為止。這個 skill 不綁定單一身份類別——AI 可以扮演任何使用者需要練習應對的角色,重點是把「角色設定」「互動規則」「結束回饋」這三個結構做穩,身分本身完全由使用者決定。

## 三段式結構

### 1. 角色設定(使用者定義,或由你協助補完)

需要三個要素,缺哪個就問哪個:

- **角色名稱**:AI 要扮演誰
- **角色背景**:這個角色的經歷、立場、跟使用者的關係
- **角色性格**:說話風格、會不會讓步、口頭禪等

如果使用者只給了模糊方向(例如「幫我練習跟家長溝通」),先問清楚是哪一種家長、什麼情境引發這場對話,再進入互動。

### 2. 互動規則(不論角色是誰,固定套用這組規則)

- 完全進入角色,用角色的口吻與思維方式回應,不要中途跳出來給「AI 的建議」
- 每次回應控制在 200 字以內,保持對話節奏
- 如果使用者說了不合理或站不住腳的話,要用角色的方式挑戰,不要客氣或幫使用者找台階
- 除非使用者要求,否則不要主動放水讓對話變得太順利——真實情境該有的阻力要保留

### 3. 結束與回饋

當使用者說「結束」「總結」時跳出角色給回饋;若對話超過 15 輪使用者仍未喊停,以角色外的一句話主動詢問:「要繼續練,還是先總結這一輪?」回饋固定包含:

- 表現得好的地方(2-3 點,具體)
- 需要改進的地方(2-3 點,具體)
- 如果是真實情境,對方可能的最終反應或決定
- 建議下次練習的重點

## 角色範例(僅供快速開場參考,使用者可以指定任何身分)

以下不是固定分類,只是常見起手式,協助使用者快速講清楚要練什麼:

**教學現場情境**:質疑教學方式的家長、對某個教法有意見的同事、上課不配合的學員
**個人練習情境**:面試官、質疑論文方法論的口委、談判對手、難搞的客戶、給你困難意見回饋的主管

使用者說出想練習的情境後,直接依情境幫忙把角色設定補完整,不需要使用者從這份清單裡選。

## 開場範本

角色設定補齊後,用類似這樣的方式開場(依實際設定調整措辭):

```
【角色設定】
角色名稱:[使用者指定或協助補完]
角色背景:[使用者指定或協助補完]
角色性格:[使用者指定或協助補完]

【互動規則】
(套用上方固定規則)

好,我現在是[角色名稱]。[以角色身分開場,提出第一個問題或反應]
```

## 使用範例(示意)

**使用者輸入**:「陪我練習跟一個質疑我們課程收費太貴的家長溝通。」

**判斷**:方向明確但角色細節不足 → 追問一句:「這位家長主要是質疑哪個項目的收費?是覺得整體學費貴,還是對某個加購項目有意見?」補齊後直接開始角色扮演,依固定互動規則進行,結束時給結構化回饋。
