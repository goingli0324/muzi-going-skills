# Muzi-Going Skills

Muzi Going 的 Claude skills 商店(Claude Code plugin marketplace)。

## 安裝

在 Claude Code 裡加入這個 marketplace(加一次就好):

```
/plugin marketplace add goingli0324/muzi-going-skills
```

之後用 `/plugin` 瀏覽與安裝這裡的 skills,更新也會自動跟上。

## 目前收錄

| Skill | 分類 | 說明 |
|---|---|---|
| [prompt-coach](plugins/prompt-coach) | productivity | 問對問題教練——把模糊請求轉譯成「目標/限制/障礙」三要素,收斂成可直接使用的結構化 prompt |
| [multi-perspective-panel](plugins/multi-perspective-panel) | productivity | 多角度組隊思考——批判/創意/溝通/互動四角色檢視同一個決策,平行分析或紅藍隊辯論 |
| [ai-roleplay-practice](plugins/ai-roleplay-practice) | learning | AI 角色扮演練習夥伴——AI 扮演任何指定角色陪練困難對話,結束給結構化回饋 |
| [pdca-process-review](plugins/pdca-process-review) | productivity | PDCA 流程檢視——用戴明循環檢視與優化任何反覆執行的流程,找出卡點與改善方向 |
| [agentic-dev-loop](plugins/agentic-dev-loop) | development | 系統化開發工作流——研究 → plan.md → 實作 → Verify 雙閘 → 部署,串接下面三個 skill 的編排器 |
| [project-guardrails](plugins/project-guardrails) | development | 連動禁區防護——分析程式碼找出「改 A 壞 B」高風險區,寫入專案 CLAUDE.md |
| [ui-ux-deploy-reviewer](plugins/ui-ux-deploy-reviewer) | design | 部署前 UI/UX 總體檢——20 項原則逐項審視,輸出問題清單與放行檢核表 |
| [web-security-reviewer](plugins/web-security-reviewer) | security | 防禦性安全審查——檢測資安漏洞、資料外洩、壓力/效能風險,輸出依嚴重度排序的報告與修正後程式碼(GAS/前端/後端) |

## 單獨安裝(不透過 marketplace)

每個 skill 也有獨立 repo,可直接 clone 到 `~/.claude/skills/`:

- https://github.com/goingli0324/prompt-coach
- https://github.com/goingli0324/multi-perspective-panel
- https://github.com/goingli0324/ai-roleplay-practice
- https://github.com/goingli0324/pdca-process-review
- https://github.com/goingli0324/agentic-dev-loop
- https://github.com/goingli0324/project-guardrails
- https://github.com/goingli0324/ui-ux-deploy-reviewer
- https://github.com/goingli0324/web-security-reviewer

Claude App / claude.ai 使用者:把 skill 資料夾壓成 `.skill`(ZIP)檔,到 **Settings → Skills** 上傳。

## License

MIT — see [LICENSE](LICENSE).
