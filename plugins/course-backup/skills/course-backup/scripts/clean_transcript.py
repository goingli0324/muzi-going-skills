#!/usr/bin/env python3
"""
把 scripts/transcribe.py（faster-whisper）產生的 `_逐字稿.md` 整理成與平台字幕同格式的乾淨版。

兩個階段，對應 SKILL.md Step 6.5：

  prep   機械正規化：去掉檔頭 metadata 與檔尾「疑似重複」附註、OpenCC s2twp、臺→台、半形逗號／問號改全形。
         輸出 <n>.prep.txt 給校對 agent 讀。
  final  校對 agent 寫完 <n>.校對.txt 後：驗證行數與 prep 一致、加來源說明行、依 mp4 檔名輸出
         `<單元>.逐字稿.txt` 到章資料夾。

    python3 clean_transcript.py prep  "<章資料夾>/1-2 xxx_逐字稿.md" --workdir <工作目錄>/ch1
    python3 clean_transcript.py final <工作目錄>/ch1/1-2.校對.txt --chapter "<章資料夾>"

行數必須一致的理由：校對只准改字不准併行，行數一變就代表有內容被吞掉或加進去，這是唯一便宜又可靠的守門。
"""
import argparse, os, re, sys

try:
    import opencc
    _cc = opencc.OpenCC('s2twp')
except ImportError:
    _cc = None
    print('[警告] 沒有 opencc，略過簡繁轉換（pip3 install opencc-python-reimplemented）', file=sys.stderr)

PROVENANCE = '（本機語音辨識產生，已做繁體正規化與錯字校對，未逐句對照音檔；原始輸出見同名 _逐字稿.md）'
# s2twp 會把幾個台灣本來就用的詞轉壞，轉完要還原
S2TWP_OVERREACH = {'許可權': '權限', '繫結': '綁定', '透過': '通過'}  # 「透過」只在「驗證透過」類語境是錯的，final 前由校對員判斷


def unit_no(name):
    m = re.match(r'(\d+-\d+)', os.path.basename(name))
    if not m:
        sys.exit(f'檔名開頭要是單元編號（如 1-2）：{name}')
    return m.group(1)


def prep(src, workdir):
    t = open(src).read()
    first = t.split('\n')[0]
    title = re.split(r'[|｜]', first, 1)[1].strip() if re.search(r'[|｜]', first) else unit_no(src)
    body = t.split('---', 1)[1] if '---' in t else t            # 去檔頭 metadata
    body = re.split(r'\n---\n', body.strip(), 1)[0].strip()      # 去檔尾附註表格
    if _cc:
        body = _cc.convert(body)
    body = body.replace('臺', '台').replace(',', '，').replace('?', '？')
    for k, v in S2TWP_OVERREACH.items():
        if k != '透過':
            body = body.replace(k, v)
    os.makedirs(workdir, exist_ok=True)
    out = os.path.join(workdir, unit_no(src) + '.prep.txt')
    open(out, 'w').write(title + '\n\n' + body + '\n')
    print(out, body.count('\n') + 1, 'lines')


def final(proof, chapter):
    n = unit_no(proof)
    prep_file = os.path.join(os.path.dirname(proof), n + '.prep.txt')
    a = open(prep_file).read().rstrip('\n').split('\n')
    b = open(proof).read().rstrip('\n').split('\n')
    if len(a) != len(b):
        sys.exit(f'[擋下] 行數不一致：prep {len(a)} 行、校對 {len(b)} 行。校對只准改字，去看哪一行被併掉或多出來。')
    if b[0] != a[0]:
        sys.exit('[擋下] 第一行標題被改動')
    b.insert(1, PROVENANCE)
    mp4 = [f for f in os.listdir(chapter) if f.startswith(n + ' ') and f.endswith('.mp4')]
    if not mp4:
        sys.exit(f'[擋下] 章資料夾裡找不到 {n} 開頭的 mp4，無法決定輸出檔名')
    out = os.path.join(chapter, mp4[0][:-4] + '.逐字稿.txt')
    open(out, 'w').write('\n'.join(b) + '\n')
    print(out, len(b), 'lines')


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('prep'); p.add_argument('src'); p.add_argument('--workdir', required=True)
    f = sub.add_parser('final'); f.add_argument('proof'); f.add_argument('--chapter', required=True)
    a = ap.parse_args()
    prep(a.src, a.workdir) if a.cmd == 'prep' else final(a.proof, a.chapter)


if __name__ == '__main__':
    main()
