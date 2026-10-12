#!/usr/bin/env python3
"""
線上課程備份的本機下載器。輸入 manifest.json（格式見 references/manifest-schema.md）。

    python3 download_manifest.py manifest.json --dest ~/course-backup
    python3 download_manifest.py manifest.json --dest ... --verify      # 只驗證＋重建目錄.md
    python3 download_manifest.py manifest.json --dest ... --workers 4   # 影片並行數

下載順序刻意固定：講義 → 字幕 → 影片。理由是簽名網址時效不同——S3 講義常常只有 10 分鐘，
CloudFront 影片約 100 分鐘；先把最快過期的抓完，再慢慢拉大檔。已完成且大小／時長正確的檔案會跳過，
所以簽名過期後重簽、重跑就好。

需要：ffmpeg、ffprobe、curl；youtube 型別另需 yt-dlp。
"""
import argparse, json, os, re, shutil, subprocess, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = {'User-Agent': 'Mozilla/5.0'}


def safe(s, n=80):
    return re.sub(r'[/\\:*?"<>|]', '_', s or '').strip()[:n]


def get(url, timeout=60):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()


def curl(url, out):
    r = subprocess.run(['curl', '-sS', '-L', '-o', out, '-w', '%{http_code}', url], capture_output=True, text=True)
    return r.stdout.strip()


def probe_duration(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def vtt_to_txt(vtt):
    lines = []
    for l in vtt.replace('\r', '').split('\n'):
        l = l.strip()
        if not l or l == 'WEBVTT' or '-->' in l or l.isdigit() or l.startswith(('NOTE', 'STYLE', 'Kind:', 'Language:')):
            continue
        l = re.sub(r'<[^>]+>', '', l)
        if not lines or lines[-1] != l:
            lines.append(l)
    return '\n'.join(lines)


def video_ok(path, expected):
    if not os.path.exists(path) or os.path.getsize(path) < 1e5:
        return False
    if expected:
        d = probe_duration(path)
        return d is not None and abs(d - expected) <= 5
    return probe_duration(path) is not None


# ---------- 各型別的影片下載 ----------

def dl_hls(v, out):
    url = v['url']
    path, query = (url.split('?', 1) + [''])[:2]
    master = get(url).decode()
    if re.search(r'#EXT-X-KEY:METHOD=SAMPLE-AES|#EXT-X-SESSION-KEY', master):
        raise RuntimeError('DRM (SAMPLE-AES) — 不下載')
    variants = [l.strip() for l in master.split('\n') if l.strip() and not l.startswith('#')]
    if not variants:
        raise RuntimeError('master 沒有變體')
    var = next((x for x in variants if v.get('prefer', '1080') in x), variants[0])
    base = path.rsplit('/', 1)[0] + '/'
    vurl = var if var.startswith('http') else base + var.split('?')[0]
    vq = var.split('?', 1)[1] if '?' in var else query
    playlist = get(vurl + ('?' + vq if vq else '')).decode()
    if re.search(r'#EXT-X-KEY:METHOD=SAMPLE-AES', playlist):
        raise RuntimeError('DRM (SAMPLE-AES) — 不下載')
    vbase = vurl.rsplit('/', 1)[0] + '/'
    local = []
    for l in playlist.split('\n'):
        s = l.strip()
        if s and not s.startswith('#'):
            if not s.startswith('http'):
                s = vbase + s
            if '?' not in s and vq:
                s += '?' + vq
            local.append(s)
        else:
            local.append(l)
    lp = out + '.local.m3u8'
    open(lp, 'w').write('\n'.join(local))
    r = subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-protocol_whitelist', 'file,http,https,tcp,tls',
                        '-i', lp, '-c', 'copy', '-bsf:a', 'aac_adtstoasc', out], capture_output=True, text=True, timeout=7200)
    os.remove(lp)
    if r.returncode != 0:
        raise RuntimeError('ffmpeg: ' + r.stderr[-300:])


def dl_mp4(v, out):
    code = curl(v['url'], out)
    if code != '200':
        raise RuntimeError('HTTP ' + code)


def dl_youtube(v, out, unit_base):
    if not shutil.which('yt-dlp'):
        raise RuntimeError('缺 yt-dlp（brew install yt-dlp）')
    cmd = ['yt-dlp', '-q', '--no-warnings', '-f', 'bv*[height<=1080]+ba/b', '--merge-output-format', 'mp4',
           '--write-subs', '--write-auto-subs', '--sub-langs', 'zh-TW,zh-Hant,zh,zh-Hans,en', '--sub-format', 'vtt',
           '-o', unit_base + '.%(ext)s', v['url']]
    if v.get('referer'):
        cmd += ['--referer', v['referer']]
    if v.get('cookies_from_browser'):
        cmd += ['--cookies-from-browser', v['cookies_from_browser']]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    if r.returncode != 0:
        raise RuntimeError('yt-dlp: ' + r.stderr[-300:])
    # 字幕統一改名成 <單元>.zh.vtt 並轉純文字
    d = os.path.dirname(unit_base) or '.'
    for f in sorted(os.listdir(d)):
        full = os.path.join(d, f)
        if full.startswith(unit_base + '.') and f.endswith('.vtt') and not f.endswith('.zh.vtt'):
            os.replace(full, unit_base + '.zh.vtt')
            open(unit_base + '.逐字稿.txt', 'w').write(os.path.basename(unit_base) + '\n\n' + vtt_to_txt(open(unit_base + '.zh.vtt').read()))
            break


# ---------- 主流程 ----------

def unit_paths(dest, ch, u):
    cdir = os.path.join(dest, safe(ch['title'], 60))
    return cdir, os.path.join(cdir, safe(u['title']))


def download_materials(m, dest):
    ok = fail = skip = 0
    for ch in m['chapters']:
        for u in ch['units']:
            for mt in u.get('materials') or []:
                cdir, _ = unit_paths(dest, ch, u)
                mdir = os.path.join(cdir, '講義')
                os.makedirs(mdir, exist_ok=True)
                out = os.path.join(mdir, safe(mt['name'], 120))
                size = int(mt.get('size') or 0)
                if os.path.exists(out) and (not size or os.path.getsize(out) == size):
                    skip += 1
                    continue
                if not mt.get('url'):
                    fail += 1
                    print('  講義缺網址:', mt['name'])
                    continue
                code = curl(mt['url'], out)
                if code == '200' and (not size or os.path.getsize(out) == size):
                    ok += 1
                else:
                    fail += 1
                    print(f'  講義失敗 HTTP {code}: {mt["name"]}（重簽後重跑）')
    print(f'講義：新下載 {ok}、已存在 {skip}、失敗 {fail}', flush=True)


def download_captions(m, dest):
    n = 0
    for ch in m['chapters']:
        for u in ch['units']:
            cdir, base = unit_paths(dest, ch, u)
            for j, c in enumerate(u.get('captions') or []):
                os.makedirs(cdir, exist_ok=True)
                out = base + ('.zh.vtt' if j == 0 else f'.{c.get("lang", j)}.vtt')
                if os.path.exists(out):
                    continue
                try:
                    vtt = get(c['url']).decode('utf-8', 'replace')
                except Exception as e:
                    print('  字幕失敗:', u['title'][:30], e)
                    continue
                open(out, 'w').write(vtt)
                if j == 0:
                    open(base + '.逐字稿.txt', 'w').write(u['title'] + '\n\n' + vtt_to_txt(vtt))
                n += 1
            if (u.get('notes') or '').strip():
                os.makedirs(cdir, exist_ok=True)
                open(base + '.單元說明.txt', 'w').write(u['title'] + '\n\n' + u['notes'].strip() + '\n')
    print(f'字幕：新下載 {n}', flush=True)


def video_jobs(m, dest):
    jobs = []
    for ch in m['chapters']:
        for u in ch['units']:
            cdir, base = unit_paths(dest, ch, u)
            for i, v in enumerate(u.get('videos') or []):
                b = base + ('' if i == 0 else f'_{i + 1}')
                jobs.append((u, v, cdir, b))
    return jobs


def run_video(job):
    u, v, cdir, b = job
    out = b + '.mp4'
    os.makedirs(cdir, exist_ok=True)
    if video_ok(out, u.get('duration')):
        return (u['title'][:40], 'skip')
    try:
        t = v.get('type', 'hls')
        if t == 'hls':
            dl_hls(v, out)
        elif t == 'mp4':
            dl_mp4(v, out)
        elif t == 'youtube':
            dl_youtube(v, out, b)
        else:
            return (u['title'][:40], 'unknown-type', t)
        d = probe_duration(out)
        exp = u.get('duration')
        if exp and (d is None or abs(d - exp) > 5):
            return (u['title'][:40], 'duration-mismatch', d, exp)
        return (u['title'][:40], 'ok', round(os.path.getsize(out) / 1e6), 'MB')
    except Exception as e:
        return (u['title'][:40], 'error', str(e)[:200])


def write_index(m, dest):
    L = [f'# {m["course"]} 備份目錄', '', f'來源：{m.get("source", "")}　備份日期：{time.strftime("%Y-%m-%d")}', '',
         '每章資料夾內：`單元.mp4`（影片）、`單元.zh.vtt`（平台字幕）、`單元.逐字稿.txt`（字幕轉純文字；`_逐字稿.md` 是本機模型補做、未經校對）、`講義/`（PDF）。', '']
    for ch in m['chapters']:
        L += [f'## {ch["title"]}', '']
        mats = sorted({mt['name'] for u in ch['units'] for mt in (u.get('materials') or [])})
        if mats:
            L += ['講義：' + '、'.join(mats), '']
        for u in ch['units']:
            mins = round((u.get('duration') or 0) / 60)
            cap = '有字幕' if u.get('captions') else ('無字幕，需本機補逐字稿' if u.get('videos') else '無影片')
            L.append(f'- {u["title"]}　（約 {mins} 分鐘，{cap}）')
        L.append('')
    open(os.path.join(dest, '目錄.md'), 'w').write('\n'.join(L))


def verify(m, dest):
    vids = mism = vtt = pdf = pdfbad = 0
    missing = []
    for ch in m['chapters']:
        for u in ch['units']:
            cdir, base = unit_paths(dest, ch, u)
            for i, v in enumerate(u.get('videos') or []):
                b = base + ('' if i == 0 else f'_{i + 1}')
                if not os.path.exists(b + '.mp4'):
                    missing.append(u['title'][:30])
                    continue
                vids += 1
                if not video_ok(b + '.mp4', u.get('duration')):
                    mism += 1
            if u.get('captions') and os.path.exists(base + '.zh.vtt'):
                vtt += 1
            for mt in u.get('materials') or []:
                f = os.path.join(cdir, '講義', safe(mt['name'], 120))
                if os.path.exists(f):
                    pdf += 1
                    if mt.get('size') and os.path.getsize(f) != int(mt['size']):
                        pdfbad += 1
    leftover = sum(1 for r, _, fs in os.walk(dest) for f in fs if f.endswith('.local.m3u8'))
    print(f'影片 {vids} 支（缺 {len(missing)}，時長不符 {mism}）｜字幕 {vtt}｜講義 {pdf}（大小不符 {pdfbad}）｜殘留 m3u8 {leftover}')
    if missing:
        print('缺影片：', missing)
    no_cap = [u['title'][:30] for ch in m['chapters'] for u in ch['units'] if u.get('videos') and not u.get('captions')]
    if no_cap:
        print('無平台字幕、需本機補逐字稿：', no_cap)
    return not missing and mism == 0 and pdfbad == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('manifest')
    ap.add_argument('--dest', required=True, help='根目錄，課程名資料夾會建在底下')
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--verify', action='store_true', help='只驗證與重建目錄.md')
    a = ap.parse_args()
    m = json.load(open(a.manifest))
    dest = os.path.join(a.dest, safe(m['course'], 60))
    os.makedirs(dest, exist_ok=True)
    if not a.verify:
        shutil.copy(a.manifest, os.path.join(dest, 'manifest.json'))
        download_materials(m, dest)
        download_captions(m, dest)
        jobs = video_jobs(m, dest)
        print(f'影片：{len(jobs)} 支，{a.workers} 路並行', flush=True)
        with ThreadPoolExecutor(a.workers) as ex:
            for res in ex.map(run_video, jobs):
                print(time.strftime('%H:%M:%S'), res, flush=True)
    write_index(m, dest)
    ok = verify(m, dest)
    print('落地：', dest)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
