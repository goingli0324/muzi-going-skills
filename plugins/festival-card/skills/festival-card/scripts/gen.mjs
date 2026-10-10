// 多圖輸入生圖：餵 0~N 張參考圖 + 一段 prompt，輸出一張圖。
// 用法：node gen.mjs --out <輸出> [--ratio 3:4] [--img <圖>]... --prompt "<prompt>"
// 每次呼叫開新的 chat session——共用 session 會累積色偏漂移（貼圖產線的教訓）。
import * as fs from 'fs';
import * as path from 'path';

const HOME = process.env.HOME || '';
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const WORK = process.env.FESTIVAL_CARD_HOME ? path.resolve(process.env.FESTIVAL_CARD_HOME.replace(/^~/, HOME)) : ROOT;  // 使用者資料夾，見 cards.py

// Gemini SDK：優先用這個資料夾 npm install 的；沒有的話退回 ~/.config/gemini-mcp/vendor 那份（有裝 gemini MCP 的人可省一次安裝）
async function loadGenAI() {
  try {
    return await import('@google/genai');
  } catch {
    const vendored = path.join(HOME, '.config/gemini-mcp/vendor/node_modules/@google/genai/dist/node/index.mjs');
    if (fs.existsSync(vendored)) return await import(vendored);
    console.error(`✗ 找不到 @google/genai：在 ${ROOT} 執行 npm install`);
    process.exit(2);
  }
}
const { GoogleGenAI, Modality } = await loadGenAI();

// 金鑰順序：環境變數 GEMINI_API_KEY → GEMINI_KEY_FILE 指定的檔 → 專案 .env → ~/.config/gemini-mcp/secrets.env
// 檔案只讀不寫；金鑰不印出來
function loadKeyFile(file) {
  for (const line of fs.readFileSync(file, 'utf-8').split('\n')) {
    const t = line.trim();
    if (t && !t.startsWith('#') && t.includes('=')) {
      const i = t.indexOf('=');
      const k = t.slice(0, i).trim();
      if (!process.env[k]) process.env[k] = t.slice(i + 1).trim().replace(/^["']|["']$/g, '');
    }
  }
}
if (!process.env.GEMINI_API_KEY) {
  const candidates = [process.env.GEMINI_KEY_FILE, path.join(WORK, '.env'), path.join(HOME, '.config/gemini-mcp/secrets.env')];
  const file = candidates.find((f) => f && fs.existsSync(f));
  if (file) loadKeyFile(file);
}
if (!process.env.GEMINI_API_KEY) {
  console.error(`✗ 沒有 GEMINI_API_KEY：設環境變數，或在 ${path.join(WORK, '.env')} 寫一行 GEMINI_API_KEY=你的金鑰`);
  process.exit(2);
}

const args = process.argv.slice(2);
const imgs = [];
let out, ratio, prompt;
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--img') imgs.push(args[++i]);
  else if (args[i] === '--out') out = args[++i];
  else if (args[i] === '--ratio') ratio = args[++i];
  else if (args[i] === '--prompt') prompt = args[++i];
}
if (!out || !prompt) { console.error('需要 --out 與 --prompt'); process.exit(2); }

const MIME = { '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp' };
const parts = imgs.map((p) => ({
  inlineData: { mimeType: MIME[path.extname(p).toLowerCase()] || 'image/jpeg', data: fs.readFileSync(p).toString('base64') },
}));
parts.push({ text: prompt });

const genAI = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
const model = process.env.GEMINI_IMAGE_MODEL || 'gemini-3-pro-image-preview';
const imageConfig = { imageSize: '2K', ...(ratio ? { aspectRatio: ratio } : {}) };

const MAX_ATTEMPTS = 3;
for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
  try {
    const chat = genAI.chats.create({ model, config: { responseModalities: [Modality.TEXT, Modality.IMAGE], imageConfig } });
    const res = await chat.sendMessage({ message: parts });
    for (const p of res.candidates?.[0]?.content?.parts || []) {
      if (p.inlineData) {
        fs.mkdirSync(path.dirname(out), { recursive: true });
        fs.writeFileSync(out, Buffer.from(p.inlineData.data, 'base64'));
        console.log(`✓ ${out}`);
        process.exit(0);
      }
      if (p.text) console.log(`模型回話：${p.text.slice(0, 200)}`);
    }
    console.log(`第 ${attempt} 次回應沒有圖片`);
  } catch (e) {
    console.log(`第 ${attempt} 次失敗：${e.message?.slice(0, 160)}`);
  }
}
console.error(`✗ ${MAX_ATTEMPTS} 次都沒生出圖：${out}`);
process.exit(1);
