# 角色一致性（Character Lock）

生圖與生影片最常見的失敗是換臉、臉部漂移、角色在鏡頭之間變樣。
對策是在提示詞**最前面**放一段「角色鎖定」，後面才接畫面描述。

## 鎖定段的四件組

不論強度高低，一段有效的角色鎖定都由四個部分組成：

1. **參考宣告** — 指明「上傳的照片是唯一的身份參考」（`Use the uploaded photo as the ONLY identity reference`）
2. **保留清單** — 逐項列出不准變的特徵：臉型、五官形狀、膚色、髮型、眼鏡、體型、年齡感。**逐項列**比「保持長相」有效
3. **禁止清單** — 列出模型常見的偷跑行為並逐一禁止：美化、風格化、重新設計、換人、改年齡、改性別
4. **優先級宣告** — 明講身份一致性高於一切視覺效果（`Identity preservation priority: MAXIMUM. The uploaded face is more important than all cinematic effects.`）

強度差別只在寫多寫少：

| 情況 | 用哪種強度 |
|---|---|
| 多鏡頭影片、模型一直不聽話、真人肖像必須認得出來 | 完整版：四件組全上，保留與禁止清單逐項展開 |
| 日常生圖、單張、參考照清楚 | 精簡版：四件組各留 2–3 行 |
| 真人轉 Q 版／公仔但要保住辨識度 | 公仔化版（見 §2） |
| 已有定裝圖要讓它動起來 | 圖轉影片版（見 §3） |

寫中文提示詞時，英文鎖定前綴照樣可用——多數模型吃得下混語。

## §1 完整版範例（英文，原創範例：夜市燈籠街騎鯉魚）

```
IMPORTANT CHARACTER LOCK
Use the uploaded photograph as the ONLY identity reference.
The rider MUST be the exact same person from the uploaded photo.
Preserve 100% of: face shape, facial structure, eye shape, nose shape,
mouth shape, skin tone, hairstyle, facial proportions, identity recognition.
Do NOT beautify. Do NOT stylize. Do NOT redesign.
Do NOT replace with another person. Do NOT change age, gender, or ethnicity.
No face drift. No identity drift. No morphing.
Identity consistency throughout the entire sequence.
Identity preservation priority: MAXIMUM.
The uploaded face is more important than all cinematic effects.
────────────────────
SCENE
The exact same uploaded person rides a giant glowing koi fish,
gliding low over a rain-washed night-market street lined with red lanterns.
Steam rises from food stalls below; neon signs reflect on the wet pavement.
The koi's scales shimmer gold and vermilion; translucent fins trail like silk.
Camera tracks alongside, then cranes up to reveal the whole lantern street.
────────────────────
STYLE
Ultra realistic, cinematic, volumetric lighting, wet-surface reflections,
shallow depth of field, 8K HDR, photorealistic, award-winning cinematography.
────────────────────
NEGATIVE PROMPT
cartoon, anime, low quality, blurry face, face drift, identity drift,
face morphing, beautified face, different person, watermark, logo, text,
subtitle, camera shake, flicker, deformed face, unrecognizable face
```

## §2 公仔化版（真人轉 Q 版）

關鍵在同時要求 `keep original face identity` 與 `stylized proportions`——
這兩件事本來衝突，靠並列描述逼模型折衷。範例（原創）：

```
Use the provided photo as reference. Keep original face identity,
preserve facial features and likeness, maintain hairstyle and overall appearance.
Chibi style character, cute 3D figure, big expressive eyes, rounded face,
small body with slightly oversized head, stylized proportions,
toy-like smooth texture, clean polished rendering.
Outfit based on the original photo, simplified but keeping key details.
Background simplified from the original photo, keep the lighting mood.
Soft studio lighting, 3D render, 8K, collectible figurine style,
suitable for a personal branding mascot.
Negative: low quality, bad anatomy, asymmetrical eyes, deformed face,
losing likeness, generic doll face, messy background.
```

## §3 圖轉影片版

一致性要求寫在**第一句**，後面接分秒分鏡。範例（原創，中文）：

```
生成影片：保持人物臉部、五官、髮型、服裝與整體造型完全一致，不更換人物身份。

深夜頂樓天台，人物抱著木吉他坐在水塔旁的摺疊椅上自彈自唱，
城市燈海在背後失焦成暖色光點，幾隻螢火蟲繞著身旁的露營燈飛。

0–3 秒：特寫手指撥弦，琴身反射路燈暖光。
3–6 秒：鏡頭緩慢後拉至半身，人物閉眼唱歌，微風吹動頭髮。
6–9 秒：無人機視角緩慢上升環繞，帶出整個天台與城市夜景，人物抬頭看向遠方。

Camera：slow dolly out 接 15° orbit，收在人物半身特寫。
Style：cinematic, warm tones, volumetric light, bokeh, ultra detailed, 4K。
Negative：no face change, no deformed hands, no flicker, no extra fingers,
keep identity consistent, keep outfit consistent。9:16
```

**續拍**（同一角色、下一段動作）：開頭固定一句
`Keep the exact same person, face, hairstyle, outfit and identity.`，
然後只描述新的動作與鏡頭；姿勢改變幅度大時，把「不要的舊姿勢」列進負面
（例如要角色起身飛行，就在負面加 `standing, idle, static pose, feet touching ground`）。

## §4 多角色同框

兩個以上角色時，用**條件句**涵蓋不同素材類型，讓同一段提示詞能重複套用：

- 如果參考角色是真人，就保持真人
- 如果是 Q 版人物，就保持 Q 版
- 如果是 3D 動畫角色，就保持 3D
- 如果是動物，就保持原本動物外型，但必須具有明確擬人化表演能力

並明確寫出：全片只能出現角色 A 與角色 B，禁止新增第三角色；
禁止換臉、禁止改變角色類型、禁止角色在不同場景突然改變造型或物種。
