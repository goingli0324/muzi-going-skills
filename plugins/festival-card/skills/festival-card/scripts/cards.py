"""節慶祝賀卡片產線。

  draft   <plan.json>          生 4 張直式候選 → 疊字 → 對照圖（每張一隻特有種）
  extend  <run_dir> <編號 1-4> [square|landscape]  把選中的那張延伸成橫式與正方形（可只做一種）→ 疊字
  compose <run_dir>            只重疊字（改祝賀詞時用，不重新生圖）

AI 不寫中文字：生圖一律要求無字，祝賀詞全靠 compose 疊上去。
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageStat

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "scripts" / "gen.mjs"
# 程式（ROOT）與使用者資料（WORK：角色設定、參考圖、節慶表、企劃、成品、字型）分開放：
# 做成 plugin 後程式在快取資料夾、更新會被整個覆蓋，資料不能跟著放在那裡。沒設就是同一個資料夾。
WORK = Path(os.environ.get("FESTIVAL_CARD_HOME", ROOT)).expanduser()

# 主角、動物、署名、字型都讀角色設定檔，程式裡不寫死任何人的角色（2026-10-10 為了做成 plugin 抽出來）
CHARACTER_FILE = Path(os.environ.get("FESTIVAL_CARD_CHARACTER", WORK / "character.json"))
if not CHARACTER_FILE.exists():
    sys.exit(f"✗ 找不到角色設定 {CHARACTER_FILE}：複製 character.example.json 成 character.json 再填")
CHARACTER = json.loads(CHARACTER_FILE.read_text(encoding="utf-8"))
PROTAGONIST = CHARACTER["protagonist"]

FONT_DIRS = [WORK / "fonts", Path.home() / "Library/Fonts", Path("/Library/Fonts"),
             Path.home() / ".local/share/fonts", Path("/usr/share/fonts")]


def find_font(name: str) -> Path:
    """字型可寫絕對路徑，或只寫檔名、到常見字型資料夾找。"""
    direct = Path(name).expanduser()
    if direct.is_absolute() and direct.exists():
        return direct
    for d in FONT_DIRS:
        hits = list(d.rglob(name)) if d.exists() else []
        if hits:
            return hits[0]
    raise SystemExit(f"✗ 找不到字型 {name}：放進 {WORK / 'fonts'}，或在 character.json 的 fonts 寫絕對路徑")


FONT_ZH = find_font(CHARACTER["fonts"]["zh"])
FONT_EN = find_font(CHARACTER["fonts"]["en"])
FONT_SIGN = find_font(CHARACTER["fonts"]["sign"])
# 署名可省略：沒有簽名圖就只放字樣，兩者都沒有就不放
WORDMARK = (CHARACTER.get("signature") or {}).get("wordmark") or ""
_sig = (CHARACTER.get("signature") or {}).get("image")
SIGNATURE_PNG = WORK / _sig if _sig else None

INK = (26, 29, 26)  # 品牌墨色 #1A1D1A
PAPER = (255, 255, 255)
DARK_BG_THRESHOLD = 140  # 字區平均亮度低於此改用白字

# 每種尺寸：輸出像素、生圖比例、留給字的區域（相對座標 x0,y0,x1,y1）、對齊方式、構圖指示
FORMATS = {
    "portrait": {
        "size": (1080, 1350), "ratio": "4:5", "text_box": (0.07, 0.04, 0.93, 0.25), "align": "center",
        "layout": "Vertical composition, camera pulled back. The characters are fairly small in the frame: the top "
                  "of {head_top} must be BELOW 40% of the image height, and the two characters together occupy "
                  "only the lower 55%, full bodies visible with floor below their feet. The top 35% of the image is "
                  "calm, empty background (soft wall, sky or bokeh) with no objects, heads or props in it.",
    },
    "square": {
        "size": (1080, 1080), "ratio": "1:1", "text_box": (0.08, 0.04, 0.92, 0.26), "align": "center",
        "layout": "Square composition, camera pulled back. The top of {head_top} must be BELOW 38% of the image "
                  "height; the characters occupy only the lower 58%, full bodies visible. The top 32% is calm, empty "
                  "background with no objects, heads or props in it.",
    },
    "landscape": {
        "size": (1920, 1080), "ratio": "16:9", "text_box": (0.05, 0.22, 0.45, 0.78), "align": "left",
        "layout": "Wide horizontal composition. The two characters stand together entirely inside the RIGHT half of "
                  "the frame, full bodies visible. The LEFT 47% is calm, empty background with no objects, "
                  "characters or props in it.",
    },
}

ANIMALS = {key: a["desc"] for key, a in CHARACTER["animals"].items()}
NOUN, POSSESSIVE, OBJECT = PROTAGONIST["noun"], PROTAGONIST["possessive"], PROTAGONIST["object"]

# 身分鎖：鎖五官與比例、不鎖「same face」——後者會把表情一起鎖死（手勢貼圖的教訓）
IDENTITY_LOCK = (
    f"Keep the {NOUN} the same character as in the FIRST image: {PROTAGONIST['identity']}. "
    "Keep the animal exactly as in the SECOND image: same colors, markings and toy proportions."
)


def layout(fmt: str) -> str:
    return FORMATS[fmt]["layout"].format(head_top=PROTAGONIST["head_top"])
# 留白區曾被畫成一塊平板、和下方場景之間出現硬接縫（國慶第 3 張）
SEAMLESS = ("The empty title area is simply more of the same scene (sky, wall or blurred background) and blends "
            "continuously into it - no panel, border, banner, frame, box or horizontal seam.")
NO_TEXT = "Absolutely no text, letters, numbers or Chinese characters anywhere, including on signs, books and banners."


def scene_prompt(festival: dict, card: dict, fmt: str) -> str:
    moon = festival.get("moon", "none")
    moon_rule = "Do not draw a moon." if moon == "none" else f"If the moon is visible it must be a {moon}."
    tone = festival.get("tone", "cute, cozy and heartwarming")
    return " ".join([
        f"A modern festive greeting-card illustration for {festival['name']} ({festival['meaning']}),",
        "rendered as a 3D soft vinyl designer-toy scene with the same materials and soft studio lighting "
        "as both reference images; miniature diorama feel, shallow depth of field.",
        f"Mood: {tone}. Palette: {festival['palette']}.",
        # 單張可用 motifs 覆寫節慶元素——否則莊重的日出場景也會被塞進煙火和鼓（國慶第 2 張）
        f"Scene: {card['scene']}. Festival details: {card.get('motifs', festival['motifs'])}.",
        f"The {NOUN} from the FIRST image {card['figure_action']}; {POSSESSIVE} expression is {card['expression']}.",
        f"Beside {OBJECT}, the {ANIMALS[card['animal']]} from the SECOND image {card['animal_action']}.",
        f"Exactly one {NOUN} and exactly one animal.",
        IDENTITY_LOCK, layout(fmt), SEAMLESS, moon_rule, NO_TEXT,
    ])


# 延伸改成「原圖不動、只補兩側」：讓模型重畫整張時，它會把角色重新詮釋——
# 寒露橫式連兩版都被橫向撐寬變矮胖，寫比例鎖也擋不住（使用者 2026-10-08 指出）。
# 現在直式原圖原封不動放進新畫布，模型只負責補空白處，生完再把原圖像素貼回去。
# 原圖與補景之間的漸層寬度（佔原圖寬）。墊底與貼回用同一段：
# 墊底若是硬邊，模型會把它當成畫面分界、把景物畫到那裡就切斷（霜降橫式第 3 張）
EDGE_FADE_RATIO = 0.12


def extend_prompt(fmt: str) -> str:
    side = "LEFT side" if fmt == "landscape" else "LEFT and RIGHT edges"
    return " ".join([
        f"This is a finished illustration placed on a wider canvas. The blurry smeared area on the {side} is only a "
        "placeholder. Repaint that placeholder area as a natural, seamless continuation of the same scene: "
        "same 3D soft vinyl miniature diorama render, same lighting, same depth-of-field blur, same colors.",
        # 霜降橫式第一版：模型把模糊墊底直接留下當景深，左半邊一片糊（使用者要清楚的）
        "The placeholder must NOT stay blurry: repaint it with real objects (trees, leaves, ground, props) at the same "
        "sharpness and detail level as the original area; only the far background may be as softly out of focus as "
        "the far background in the original.",
        "Do NOT change, move, redraw or resize anything in the sharp original area - the characters, their bodies, "
        "faces and props must stay pixel-identical.",
        "Do not add any new characters or animals in the extended area.",
        "Keep the extended area calm and uncluttered, since a title will be placed there.",
        NO_TEXT,
    ])


def edge_fade_mask(size, fade_left: bool, fade_right: bool) -> Image.Image:
    """原圖貼上用的遮罩：有補景的那一側，從透明漸層到不透明。"""
    w, h = size
    fade = max(8, int(w * EDGE_FADE_RATIO))
    mask = Image.new("L", size, 255)
    draw = ImageDraw.Draw(mask)
    for i in range(fade):
        alpha = int(255 * i / fade)
        if fade_left:
            draw.line([(i, 0), (i, h)], fill=alpha)
        if fade_right:
            draw.line([(w - 1 - i, 0), (w - 1 - i, h)], fill=alpha)
    return mask


def place_on_canvas(portrait: Image.Image, fmt: str):
    """把直式原圖依目標比例放上新畫布；回傳（畫布、原圖貼放位置 x）。
    空白處先用原圖拉伸後重度模糊墊底，給模型延續場景的色彩線索；原圖邊緣漸層融入，不留硬邊。"""
    W, H = FORMATS[fmt]["size"]
    canvas_h = portrait.height
    canvas_w = round(canvas_h * W / H)
    x = canvas_w - portrait.width if fmt == "landscape" else (canvas_w - portrait.width) // 2
    canvas = portrait.resize((canvas_w, canvas_h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(canvas_h // 25))
    canvas.paste(portrait, (x, 0), edge_fade_mask(portrait.size, x > 0, x + portrait.width < canvas_w))
    return canvas, x


def paste_original_back(generated: Image.Image, portrait: Image.Image, x: int) -> Image.Image:
    """模型補完後，把原圖像素蓋回去，只在接縫處做漸層，保證角色與直式版完全一致。"""
    canvas = generated.convert("RGB").resize((round(portrait.height * generated.width / generated.height),
                                              portrait.height), Image.LANCZOS)
    canvas.paste(portrait, (x, 0), edge_fade_mask(portrait.size, x > 0, x + portrait.width < canvas.width))
    return canvas


def run_gen(out: Path, ratio: str, imgs: list, prompt: str) -> bool:
    cmd = ["node", str(GEN), "--out", str(out), "--ratio", ratio, "--prompt", prompt]
    for p in imgs:
        cmd += ["--img", str(p)]
    # Node 內建 fetch 預設不讀 HTTPS_PROXY；在只能走代理的沙盒裡會 ENOTFOUND（2026-10-08 霜降）。
    # 沒設代理的環境下這個開關沒有作用。
    env = {**os.environ, "NODE_USE_ENV_PROXY": "1"}
    res = subprocess.run(cmd, capture_output=True, text=True, env=env)
    print(res.stdout.strip() or res.stderr.strip())
    if res.returncode == 0:
        save_prompt_record(out, ratio, imgs, prompt)
    return res.returncode == 0


def save_prompt_record(out: Path, ratio: str, imgs: list, prompt: str):
    """生圖成功就把實際送出的提示詞存在圖旁邊（<圖檔名>.prompt.txt）。
    之前沒存，使用者要看時只能用現行程式重建，早期幾輪會跟實際送出的有出入（2026-10-10）。"""
    lines = [f"比例：{ratio}", "參考圖（依送入順序）："]
    lines += [f"  {i}. {Path(p).name}" for i, p in enumerate(imgs, 1)] or ["  （無）"]
    lines += ["", "提示詞：", prompt, ""]
    out.with_suffix(".prompt.txt").write_text("\n".join(lines), encoding="utf-8")


def figure_path(costume) -> Path:
    """主角參考圖：設定寫成 figures/{costume}_front.png 就依節慶換造型，寫死檔名就每個節慶都用同一張。"""
    pattern = PROTAGONIST["figure"]
    return WORK / pattern.format(costume=costume or PROTAGONIST.get("default_costume") or "")


def flatten_figure(costume, dest: Path) -> Path:
    """主角 PNG 常是透明底，透明像素餵給模型可能被當成黑色——先鋪白。"""
    src = Image.open(figure_path(costume)).convert("RGBA")
    bg = Image.new("RGBA", src.size, (255, 255, 255, 255))
    Image.alpha_composite(bg, src).convert("RGB").save(dest)
    return dest


# ---------- 疊字 ----------

def cover(img: Image.Image, size) -> Image.Image:
    w, h = size
    scale = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    x = (img.width - w) // 2
    y = (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def fit_font(path: Path, lines, max_w: int, max_size: int, min_size: int):
    for size in range(max_size, min_size - 1, -2):
        font = ImageFont.truetype(str(path), size)
        if all(font.getlength(line) <= max_w for line in lines):
            return font
    return ImageFont.truetype(str(path), min_size)


ZH_MIN_SIZE, EN_MIN_SIZE = 56, 30


def fit_text_block(zh_lines, en_lines, box, W, H):
    """中英文字級：寬度與高度都要放進字區。
    原本只看寬度，兩行中文＋一行英文會往下溢出 34–80px 壓到角色的頭（2026-10-08 寒露正方形）。"""
    box_w, box_h = box[2] - box[0], box[3] - box[1]
    zh_max = int(min(W, H) * 0.10)
    while True:
        zh_font = fit_font(FONT_ZH, zh_lines, box_w, max_size=zh_max, min_size=ZH_MIN_SIZE)
        en_font = fit_font(FONT_EN, en_lines, box_w, max_size=int(zh_font.size * 0.42), min_size=EN_MIN_SIZE)
        zh_gap, en_gap, block_gap = int(zh_font.size * 0.18), int(en_font.size * 0.25), int(zh_font.size * 0.35)
        block_h = (len(zh_lines) * (zh_font.size + zh_gap) - zh_gap + block_gap
                   + len(en_lines) * (en_font.size + en_gap) - en_gap)
        if block_h <= box_h or zh_font.size <= ZH_MIN_SIZE:
            if block_h > box_h:
                print(f"⚠ 祝賀詞太長，最小字級仍超出字區 {block_h - box_h}px：{'/'.join(zh_lines)}")
            return zh_font, en_font, zh_gap, en_gap, block_gap, block_h
        zh_max = zh_font.size - 2


def draw_block(draw, lines, font, box, align, y, fill, stroke_fill, stroke, line_gap):
    x0, _, x1, _ = box
    for line in lines:
        w = font.getlength(line)
        x = x0 if align == "left" else x0 + (x1 - x0 - w) / 2
        draw.text((x, y), line, font=font, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
        y += font.size + line_gap
    return y


def tinted(mask: Image.Image, color) -> Image.Image:
    layer = Image.new("RGBA", mask.size, color + (255,))
    layer.putalpha(mask)
    return layer


def draw_signature_block(img: Image.Image):
    """右下角：簽名圖在上、署名小字在下，兩者置中成一組（character.json 的 signature，可省略）。
    依角落亮度換色——亮底用簽名原本的品牌綠配白色光暈，暗底改白字配墨色光暈。"""
    W, H = img.size
    unit = min(W, H)
    if not SIGNATURE_PNG and not WORDMARK:
        return
    if SIGNATURE_PNG:
        sig = Image.open(SIGNATURE_PNG).convert("RGBA")
        sig_w = int(unit * 0.28)
        sig = sig.resize((sig_w, round(sig.height * sig_w / sig.width)), Image.LANCZOS)
    else:
        sig = Image.new("RGBA", (1, 0))

    mark_font = ImageFont.truetype(str(FONT_SIGN), max(18, unit // 56))
    tracking = mark_font.size * 0.28  # 加字距，小字才不會糊成一團
    mark_w = sum(mark_font.getlength(ch) for ch in WORDMARK) + tracking * (len(WORDMARK) - 1) if WORDMARK else 0

    margin = int(unit * 0.035)
    gap = int(unit * 0.002)
    block_w = max(sig.width, int(mark_w))
    block_h = sig.height + gap + mark_font.size
    x0, y0 = W - margin - block_w, H - margin - block_h

    dark_bg = ImageStat.Stat(img.crop((x0, y0, W, H)).convert("L")).mean[0] < DARK_BG_THRESHOLD
    fill, halo = (PAPER, INK) if dark_bg else (None, PAPER)  # None＝保留簽名原色

    if SIGNATURE_PNG:
        alpha = sig.getchannel("A")
        glow = alpha.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(2.5))
        sig_x = x0 + (block_w - sig.width) // 2
        img.paste(tinted(glow, halo), (sig_x, y0), tinted(glow, halo))
        face = sig if fill is None else tinted(alpha, fill)
        img.paste(face, (sig_x, y0), face)

    mark_fill = fill or INK
    draw = ImageDraw.Draw(img)
    x = x0 + (block_w - mark_w) / 2
    y = y0 + sig.height + gap
    for ch in WORDMARK:
        draw.text((x, y), ch, font=mark_font, fill=mark_fill, stroke_width=1, stroke_fill=halo)
        x += mark_font.getlength(ch) + tracking


def compose_card(art_path: Path, card: dict, fmt: str, out: Path):
    spec = FORMATS[fmt]
    W, H = spec["size"]
    img = cover(Image.open(art_path).convert("RGB"), (W, H))
    fx0, fy0, fx1, fy1 = spec["text_box"]
    box = (int(fx0 * W), int(fy0 * H), int(fx1 * W), int(fy1 * H))

    dark_bg = ImageStat.Stat(img.crop(box).convert("L")).mean[0] < DARK_BG_THRESHOLD
    fill, halo = (PAPER, INK) if dark_bg else (INK, PAPER)

    zh_lines = card["zh"].split("|")
    en_lines = card["en"].split("|")
    zh_font, en_font, zh_gap, en_gap, block_gap, block_h = fit_text_block(zh_lines, en_lines, box, W, H)
    y = box[1] + max(0, (box[3] - box[1] - block_h) // 2)

    draw = ImageDraw.Draw(img)
    y = draw_block(draw, zh_lines, zh_font, box, spec["align"], y, fill, halo,
                   stroke=max(4, zh_font.size // 14), line_gap=zh_gap)
    draw_block(draw, en_lines, en_font, box, spec["align"], y - zh_gap + block_gap, fill, halo,
               stroke=max(3, en_font.size // 12), line_gap=en_gap)

    draw_signature_block(img)

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, quality=95)


def contact_sheet(paths, out: Path):
    thumbs = []
    for p in paths:
        t = Image.open(p).convert("RGB")
        t.thumbnail((540, 675))
        thumbs.append(t)
    sheet = Image.new("RGB", (sum(t.width for t in thumbs) + 20 * (len(thumbs) + 1), 675 + 90), (245, 243, 238))
    draw = ImageDraw.Draw(sheet)
    num_font = ImageFont.truetype(str(FONT_SIGN), 44)
    x = 20
    for i, t in enumerate(thumbs, 1):
        sheet.paste(t, (x, 20))
        draw.text((x + t.width // 2 - 12, 20 + t.height + 14), str(i), font=num_font, fill=INK)
        x += t.width + 20
    sheet.save(out, quality=92)


# ---------- 指令 ----------

def load_plan(run_dir: Path) -> dict:
    return json.loads((run_dir / "plan.json").read_text(encoding="utf-8"))


def festival_info(plan: dict) -> dict:
    table = json.loads((WORK / "festivals.json").read_text(encoding="utf-8"))
    info = {**table.get(plan["festival"], {}), **plan.get("overrides", {})}
    info["name"] = plan.get("festival_en", plan["festival"])
    missing = [k for k in ("meaning", "motifs", "palette") if k not in info]
    if missing:
        sys.exit(f"✗ 節慶「{plan['festival']}」缺設定 {missing}：請在 festivals.json 補一筆，或寫在 plan 的 overrides")
    return info


def cmd_draft(plan_path: Path):
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    used = [c["animal"] for c in plan["cards"]]
    unknown = sorted(set(used) - set(ANIMALS))
    if len(used) != 4 or unknown:
        sys.exit(f"✗ plan 必須剛好 4 張，且動物都要在 character.json 的 animals 裡（不認得：{unknown}）")
    if len(ANIMALS) >= 4 and len(set(used)) != 4:
        sys.exit("✗ 動物有 4 隻以上時，4 張候選要各用一隻不同的")
    info = festival_info(plan)
    run_dir = WORK / "output" / f"{plan['festival']}_{plan.get('date', date.today().isoformat())}"
    (run_dir / "raw").mkdir(parents=True, exist_ok=True)
    (run_dir / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    figure = flatten_figure(info.get("costume"), run_dir / "raw" / "figure_ref.png")

    def job(i_card):
        i, card = i_card
        out = run_dir / "raw" / f"{i}_portrait.png"
        if out.exists():
            return True
        return run_gen(out, "4:5", [figure, WORK / CHARACTER["animals"][card["animal"]]["anchor"]],
                       scene_prompt(info, card, "portrait"))

    with ThreadPoolExecutor(4) as pool:
        results = list(pool.map(job, enumerate(plan["cards"], 1)))
    if not all(results):
        sys.exit("✗ 有候選沒生出來，重跑同一個指令會只補缺的那幾張")
    cmd_compose(run_dir)
    print(f"\n對照圖：{run_dir / 'sheet.jpg'}")


def cmd_extend(run_dir: Path, n: int, only: str = None):
    plan = load_plan(run_dir)
    card = plan["cards"][n - 1]
    info = festival_info(plan)
    portrait = Image.open(run_dir / "raw" / f"{n}_portrait.png").convert("RGB")

    def job(fmt):
        out = run_dir / "raw" / f"{n}_{fmt}.png"
        if out.exists():
            return True
        canvas, x = place_on_canvas(portrait, fmt)
        placeholder = run_dir / "raw" / f"{n}_{fmt}_placeholder.png"
        canvas.save(placeholder)
        filled = run_dir / "raw" / f"{n}_{fmt}_filled.png"
        if not run_gen(filled, FORMATS[fmt]["ratio"], [placeholder], extend_prompt(fmt)):
            return False
        paste_original_back(Image.open(filled), portrait, x).save(out)
        return True

    with ThreadPoolExecutor(2) as pool:
        if not all(pool.map(job, [only] if only else ["landscape", "square"])):
            sys.exit("✗ 延伸失敗，重跑同一個指令會只補缺的")
    for fmt in ["portrait", only] if only else FORMATS:
        compose_card(run_dir / "raw" / f"{n}_{fmt}.png", card, fmt, run_dir / "cards" / f"{plan['festival']}_{n}_{fmt}.jpg")
    print(f"✓ 成品：{run_dir / 'cards'}")


def cmd_compose(run_dir: Path):
    plan = load_plan(run_dir)
    outs = []
    for i, card in enumerate(plan["cards"], 1):
        for fmt in FORMATS:
            art = run_dir / "raw" / f"{i}_{fmt}.png"
            if art.exists():
                out = run_dir / "cards" / f"{plan['festival']}_{i}_{fmt}.jpg"
                compose_card(art, card, fmt, out)
                if fmt == "portrait":
                    outs.append(out)
    contact_sheet(outs, run_dir / "sheet.jpg")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cmd, arg = sys.argv[1], Path(sys.argv[2]).expanduser().resolve()
    if cmd == "draft":
        cmd_draft(arg)
    elif cmd == "extend":
        cmd_extend(arg, int(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else None)
    elif cmd == "compose":
        cmd_compose(arg)
    else:
        sys.exit(__doc__)
