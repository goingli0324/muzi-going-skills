#!/usr/bin/env python3
"""
校對員拿不準的字，用「切片重聽」定案：切出該句前後各 1.5 秒，用三種設定重新辨識，
列出候選字的逐字信心值。三種設定都指向同一個字才算定案；分歧就留給人聽。

    python3 relisten.py "<單元>.mp4" --at 02:58 03:08 05:39 --chars 導登

--chars 是要追蹤的候選字（任何一個字出現在辨識結果的詞裡就列出信心值）。
--at 用 `_逐字稿_timestamps.md` 裡該句的起始時間，可多個。

需要 faster-whisper（large-v3）；有裝 mlx_whisper 就多跑 whisper-large-v3-turbo 當第二個模型。
"""
import argparse, os, subprocess, sys, tempfile, warnings

warnings.filterwarnings('ignore')


def sec(t):
    p = [int(x) for x in t.split(':')]
    return p[0] * 60 + p[1] if len(p) == 2 else p[0] * 3600 + p[1] * 60 + p[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('media')
    ap.add_argument('--at', nargs='+', required=True, help='mm:ss 起始時間，可多個')
    ap.add_argument('--chars', required=True, help='要追蹤的候選字，例如 導登')
    ap.add_argument('--span', type=float, default=3.0, help='每段長度（秒），預設 3')
    ap.add_argument('--pad', type=float, default=1.5, help='前後留白（秒）')
    a = ap.parse_args()

    from faster_whisper import WhisperModel
    fw = WhisperModel('large-v3', device='cpu', compute_type='int8')
    try:
        import mlx_whisper
    except ImportError:
        mlx_whisper = None

    def run_fw(path, prompt):
        segs, _ = fw.transcribe(path, language='zh', beam_size=5, word_timestamps=True,
                                initial_prompt=prompt, condition_on_previous_text=False)
        words = [w for s in segs for w in s.words]
        return ''.join(w.word for w in words), [(w.word, round(float(w.probability), 2)) for w in words if any(c in w.word for c in a.chars)]

    def run_mlx(path):
        r = mlx_whisper.transcribe(path, path_or_hf_repo='mlx-community/whisper-large-v3-turbo', language='zh', word_timestamps=True)
        key = [(w['word'], round(w.get('probability', 0), 2)) for s in r['segments'] for w in s.get('words', []) if any(c in w['word'] for c in a.chars)]
        return r['text'], key

    with tempfile.TemporaryDirectory() as td:
        for t in a.at:
            clip = os.path.join(td, t.replace(':', '') + '.wav')
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', str(max(0, sec(t) - a.pad)), '-t', str(a.span + 2 * a.pad),
                            '-i', a.media, '-ac', '1', '-ar', '16000', clip], check=True)
            print(f'\n== {t} ==')
            for label, (txt, key) in [('fw 無提示 ', run_fw(clip, None)), ('fw 中性提示', run_fw(clip, '以下是台灣講師的線上課程。'))]:
                print(f' {label}: {txt.strip()[:60]} | {key}')
            if mlx_whisper:
                txt, key = run_mlx(clip)
                print(f' mlx-turbo : {txt.strip()[:60]} | {key}')


if __name__ == '__main__':
    main()
