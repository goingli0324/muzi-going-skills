#!/usr/bin/env python3
"""
沒有平台字幕的單元，用本機 faster-whisper 補逐字稿。音檔不離開這台電腦。

    python3 transcribe.py "<章資料夾>/1-2 單元名.mp4"
    python3 transcribe.py "<單元>.mp4" --model medium --outdir "<章資料夾>"

輸出兩份，與 clean_transcript.py、relisten.py 銜接：
  <單元>_逐字稿.md             每行一句，給校對用
  <單元>_逐字稿_timestamps.md  每行 [mm:ss → mm:ss] 一句，重聽時用來找時間點

需要：pip3 install faster-whisper
第一次執行會下載模型（large-v3 約 3 GB）。M 系列 CPU、int8 時速度約與影片等長。
"""
import argparse, os, sys

# 偏向繁體中文輸出；內容刻意寫得中性，避免把模型往特定詞彙帶偏
INITIAL_PROMPT = '以下是一堂線上課程的講課錄音，請以繁體中文逐字記錄。'


def fmt(t):
    m, s = divmod(int(t), 60)
    return f'{m:02d}:{s:02d}'


def transcribe(media, model_name, outdir, language):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit('缺 faster-whisper：pip3 install faster-whisper')
    model = WhisperModel(model_name, device='auto', compute_type='int8')
    # condition_on_previous_text=False：Whisper 遇到長段靜音會開始重複上一句或吐出「感謝觀看」，
    # 而且一旦開始就沿著前文一路錯下去；關掉它能把錯誤限制在那一段。
    segments, info = model.transcribe(media, language=language, beam_size=5, vad_filter=True,
                                      initial_prompt=INITIAL_PROMPT, condition_on_previous_text=False)
    rows = [(seg.start, seg.end, seg.text.strip()) for seg in segments if seg.text.strip()]

    base = os.path.splitext(os.path.basename(media))[0]
    outdir = outdir or os.path.dirname(os.path.abspath(media))
    plain = os.path.join(outdir, base + '_逐字稿.md')
    stamped = os.path.join(outdir, base + '_逐字稿_timestamps.md')
    header = (f'# 逐字稿（模型產生，未經校對）｜{base}\n\n'
              f'> 來源：`{os.path.basename(media)}`，模型 {model_name}，長度 {fmt(info.duration)}\n\n---\n\n')
    with open(plain, 'w') as f:
        f.write(header + '\n'.join(t for _, _, t in rows) + '\n')
    with open(stamped, 'w') as f:
        f.write(header + '\n'.join(f'[{fmt(a)} → {fmt(b)}] {t}' for a, b, t in rows) + '\n')
    print(plain, len(rows), 'lines')
    print(stamped)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('media')
    ap.add_argument('--model', default='large-v3', help='tiny／small／medium／large-v3，預設 large-v3')
    ap.add_argument('--outdir', default=None, help='預設與影片同資料夾')
    ap.add_argument('--language', default='zh')
    a = ap.parse_args()
    transcribe(a.media, a.model, a.outdir, a.language)


if __name__ == '__main__':
    main()
