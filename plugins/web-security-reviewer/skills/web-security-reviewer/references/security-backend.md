# 後端 API（Node / Python / PHP / Go 等）安全檢查清單

後端是真正的信任邊界。前端能繞過，後端不能。逐類對照，大致依風險排序。

## 1. 注入（Injection）

**SQL injection**：用字串拼接組 SQL 是最危險的反模式。
- 一律用參數化查詢 / prepared statement / ORM 的綁定參數。
- 表名、欄名無法參數化時，用允許清單比對。

```python
# 危險
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
# 安全
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

**Command injection**：把使用者輸入丟進 shell（`os.system`、`exec`、`child_process.exec`）。
- 用陣列形式傳參數（`execFile` / `subprocess.run([...], shell=False)`），不要組 shell 字串。

**其他**：NoSQL injection（MongoDB 把使用者物件直接當查詢條件）、LDAP injection、Server-Side Template Injection（把使用者輸入餵進模板引擎）。

## 2. 認證（Authentication）

- 密碼雜湊用 `bcrypt` / `argon2` / `scrypt`；**絕不**用 MD5、SHA1，或明文存。
- 登入端點要有速率限制與鎖定，防暴力破解。
- JWT 常見錯誤：接受 `alg: none`、弱簽章密鑰、無過期時間、把敏感資料放進 payload（payload 只是 base64，非加密）。

## 3. 授權 / 存取控制（Access Control）

最常見且常被漏掉：
- **IDOR**：`GET /api/orders/123` 沒檢查這筆 order 是否屬於當前使用者。每個物件層級操作都要驗證擁有權。
- 缺少功能層級授權（一般使用者能呼叫管理員 API）。
- **Mass assignment**：把整個 request body 直接綁到資料模型，使用者可塞 `isAdmin: true`。用明確的欄位允許清單。

## 4. 輸入驗證

- 在伺服器端驗證所有輸入：型別、長度、範圍、格式。優先允許清單而非黑名單。
- 不要信任前端送來的任何「已驗證」標記。

## 5. 資料暴露與錯誤處理

- 對外錯誤訊息不要洩漏 stack trace、SQL 錯誤、內部路徑、套件版本。生產環境關閉 debug 模式。
- API 回應不要過度回傳（over-fetching）：別把密碼雜湊、內部欄位、其他使用者資料一起送出。

## 6. SSRF（伺服器端請求偽造）

- 後端去抓「使用者提供的 URL」時，攻擊者可讓伺服器去打內網服務（雲端 metadata endpoint、內部 API）。
- 對目標 URL 做允許清單、禁止內網／保留位址、禁止跟隨轉址到內網。

## 7. 檔案上傳與路徑操控

- 驗證檔案型別（看內容不只看副檔名）、大小；儲存在 web root 之外；不可執行。
- 路徑操控（path traversal）：使用者控制檔名／路徑含 `../` 可讀寫任意檔案。正規化並限制在指定目錄內。

## 8. 機密管理

- 金鑰、連線字串、token 放環境變數或祕密管理服務（Secrets Manager / Vault），不要進程式碼或版控。
- `.env`、設定檔不要被 web server 對外提供；確認不在 git 歷史裡。

## 9. CORS

- `Access-Control-Allow-Origin: *` 搭配 `Allow-Credentials: true` 是危險組合。
- 用明確的來源允許清單。

## 10. 安全標頭

確認有送：`Content-Security-Policy`、`Strict-Transport-Security`（HSTS）、`X-Content-Type-Options: nosniff`、`X-Frame-Options`、適當的 `Referrer-Policy`。

## 11. 相依套件

- 跑 `npm audit` / `pip-audit` / `osv-scanner` 取得**即時**漏洞結果（不要憑記憶列 CVE）。
- 鎖版本、保留 lockfile、定期更新。

## 12. 速率限制與資源耗盡

- 對外 API 要有 rate limiting，避免濫用、爆量、成本失控（細節見 stress-and-performance.md）。
- 清單型端點要有分頁上限，避免一次拉整張表。

## 13. 日誌

- 不要把密碼、token、完整個資寫進 log。
- 要記錄安全事件（登入失敗、授權拒絕）以利稽核。

## 14. 傳輸安全

- 全程 HTTPS/TLS；敏感操作不要走未加密通道。
