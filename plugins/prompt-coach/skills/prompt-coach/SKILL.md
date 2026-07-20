---
name: prompt-coach
description: Turns a vague, underspecified request into a clearly structured Goal / Constraints / Obstacle breakdown, then produces a ready-to-use structured prompt. Use this whenever the user brings a fuzzy ask ("幫我想辦法...", "有什麼方法可以...", "我不知道怎麼處理..."), asks explicitly to help them "問對問題" or structure their request, or describes a real-world problem/decision they want AI help with but haven't yet specified what success looks like, what can't change, or what the actual blocker is. Trigger this proactively — even without the user naming the skill — any time answering directly would likely produce a generic, "technically correct but not actually usable" answer rather than something tailored to their real situation.
---

# 問對問題教練 (Prompt Coach)

## 核心理念

大多數「AI 給的答案沒用」不是 AI 的問題,是問題問得太模糊。這個 skill 的工作,是在回答之前,先把模糊的請求轉譯成三個具體要素,再據此產出真正有用的結構化提問或 prompt。

## 核心框架:目標 / 限制 / 障礙

| 要素 | 定義 | 判斷標準 |
|---|---|---|
| **目標 Goal** | 使用者真正想達成的結果 | 必須具體、可驗證、最好可量化或有明確的完成定義 |
| **限制 Constraints** | 無法改變、必須接受的邊界條件 | 資源、時間、規則、他人行為等既定事實 |
| **障礙 Obstacle** | 真正卡住目標達成的那個核心難題 | 通常不是使用者最初講的表面症狀,而是往下追問一層才浮現的東西 |

**常見陷阱**:使用者常常把「限制」講成「障礙」(例如「老師會繼續傳一整包照片」是限制,不是障礙;真正的障礙可能是「缺少篩選機制」)。追問時要主動幫忙分辨這兩者,不要照單全收使用者自己的歸類。

## 判斷邏輯:先數要素數量

收到請求後,先數這句話裡目標/限制/障礙三要素已經講到幾個(定義見上表)。這個數字直接決定要不要追問、以及追問時走哪個模式——見下方表格,不要另外憑「聽起來夠不夠清楚」這種主觀判斷,以免跟下面的客觀標準打架。

## 兩種模式,依情境切換

判斷標準只看一件客觀的事:**使用者這句話裡,目標/限制/障礙三要素已經講到幾個**,不要憑語氣或熟悉度去猜使用者的心理狀態。

| 已講到的要素數 | 走哪個模式 | 做法 |
|---|---|---|
| 0 個 | 模式 A | 第一題直接問目標:「你希望達成什麼具體結果?」 |
| 1 個 | 模式 A | 針對還缺的部分追問,已講到的不重複問 |
| 2-3 個 | 模式 B | 跳過追問,直接收斂 |
| 使用者明確說「給我表單」「不要一直問我」 | 模式 B | 無論資訊量,直接跳表單,留白讓使用者自己填未講清楚的部分 |

### 模式 A:對話式引導

做法:一次只問 1-2 個最關鍵的問題(不要一次丟出三個要素的完整問卷),追問時可以善用 ask_user_input 這類工具讓使用者用選的而非用打字回答,把回答逐步組裝成三要素,每問完一輪就跟使用者確認理解是否正確,直到三要素都補齊為止。

### 模式 B:表單式框架

做法:直接輸出下面這個骨架讓使用者自己填,或使用者已經在請求裡透露了部分內容時,由你先填好推測的部分、留白使用者還沒講清楚的部分:

```
【目標】我到底想達成什麼?怎樣算成功?(盡量量化、有期限)
—

【限制】什麼是我不能動的?什麼是必須接受的現實?
—

【障礙】阻擋我達成目標的核心難題是什麼?(不是限制,是真正卡住的那個點)
—
```

## 最終產出:結構化 Prompt

不論走哪種模式,補齊三要素後,最後都要收斂成一段「可以直接拿去問 AI(或作為任務起點)」的結構化陳述,格式大致如下,依實際情境調整措辭:

```
背景:[簡述問題脈絡與為什麼會遇到這個情況]
目標:[具體、可驗證的目標]
限制:[列出無法改變的邊界條件]
真正的障礙:[核心難題,不是表面症狀]

請根據以上,提出[具體想要的產出類型,例如:可執行的方案/決策建議/替代做法比較]。
```

如果使用者的請求本身就是要問你(而不是要一段給別的 AI 的 prompt),補齊三要素後直接依此回答,不需要額外包成 prompt 格式。

## 語言與風格

預設用繁體中文,但若使用者原本用英文提問,則維持英文;三要素的專有名詞(Goal / Constraints / Obstacle)可視情境雙語並陳,方便日後套用在需要英文 prompt 的場合。

## 使用範例(示意,非固定話術)

**使用者輸入**:「我想找一個方法,讓每次要規劃課程進度都不要那麼亂。」

**判斷**:資訊不足以直接回答(不知道「亂」具體指什麼、不知道限制與障礙)→ 進入模式 A。

**追問**(一次最多 1-2 個):「『亂』具體是指哪個環節?是決定教學內容順序很亂,還是跟其他老師對進度時很亂?」

依此類推,補齊三要素後再收斂成結構化陳述並繼續協助。
