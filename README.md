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
| [web-security-reviewer](plugins/web-security-reviewer) | security | 防禦性安全審查——檢測資安漏洞、資料外洩、壓力/效能風險,輸出依嚴重度排序的報告與修正後程式碼(GAS/前端/後端) |

## 單獨安裝(不透過 marketplace)

每個 skill 也有獨立 repo,可直接 clone 到 `~/.claude/skills/`:

- https://github.com/goingli0324/prompt-coach
- https://github.com/goingli0324/web-security-reviewer

Claude App / claude.ai 使用者:把 skill 資料夾壓成 `.skill`(ZIP)檔,到 **Settings → Skills** 上傳。

## License

MIT — see [LICENSE](LICENSE).
