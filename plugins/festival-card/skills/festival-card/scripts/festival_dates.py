"""算節慶的國曆日期（台灣時間）。

  list <年>                      列出那一年 37 個節慶的日期
  due  [--days 3] [--today YYYY-MM-DD]  今天往後第 N 天是哪些節慶（排程用；沒有就不輸出）

節氣用天文計算（太陽視黃經每 15° 一個），農曆節日用農曆換算，其餘是固定或規則日期。
名稱必須跟 festivals.json 的 key 一致。
"""
import argparse
import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import ephem
from lunardate import LunarDate

ROOT = Path(__file__).resolve().parent.parent
WORK = Path(os.environ.get("FESTIVAL_CARD_HOME", ROOT)).expanduser()  # 使用者資料夾，見 cards.py
TAIPEI = timezone(timedelta(hours=8))

# 太陽視黃經（度）→ 節氣
SOLAR_TERMS = {
    315: "立春", 330: "雨水", 345: "驚蟄", 0: "春分", 15: "清明", 30: "穀雨",
    45: "立夏", 60: "小滿", 75: "芒種", 90: "夏至", 105: "小暑", 120: "大暑",
    135: "立秋", 150: "處暑", 165: "白露", 180: "秋分", 195: "寒露", 210: "霜降",
    225: "立冬", 240: "小雪", 255: "大雪", 270: "冬至", 285: "小寒", 300: "大寒",
}
LUNAR_FESTIVALS = {"春節": (1, 1), "元宵": (1, 15), "端午": (5, 5), "七夕": (7, 7),
                   "中元": (7, 15), "中秋": (8, 15), "重陽": (9, 9)}
FIXED_FESTIVALS = {"教師節": (9, 28), "父親節": (8, 8), "國慶": (10, 10), "聖誕": (12, 25)}


def sun_longitude(moment: datetime) -> float:
    """太陽視黃經（度），以當下日期為曆元——節氣的定義用的就是這個。"""
    when = ephem.Date(moment.astimezone(timezone.utc).replace(tzinfo=None))
    return float(ephem.Ecliptic(ephem.Sun(when), epoch=when).lon) * 180 / ephem.pi


def solar_term_dates(year: int) -> dict:
    """逐日找太陽黃經跨過 15° 倍數的那一天（台灣時間）。"""
    result = {}
    day = datetime(year, 1, 1, tzinfo=TAIPEI)
    prev = sun_longitude(day)
    while day.year == year:
        nxt_day = day + timedelta(days=1)
        nxt = sun_longitude(nxt_day)
        for deg, name in SOLAR_TERMS.items():
            # 處理 360→0 的繞回
            a, b = prev, nxt if nxt >= prev else nxt + 360
            target = deg if deg >= a else deg + 360
            if a < target <= b:
                lo, hi = day, nxt_day  # 二分到分鐘，再取台灣日期
                for _ in range(20):
                    mid = lo + (hi - lo) / 2
                    m = sun_longitude(mid)
                    m = m if m >= a else m + 360
                    lo, hi = (mid, hi) if m < target else (lo, mid)
                result[name] = hi.astimezone(TAIPEI).date()
        day, prev = nxt_day, nxt
    return result


def festival_dates(year: int) -> dict:
    dates = solar_term_dates(year)
    for name, (m, d) in LUNAR_FESTIVALS.items():
        dates[name] = LunarDate(year, m, d).to_solar_date()
    dates["除夕"] = dates["春節"] - timedelta(days=1)
    for name, (m, d) in FIXED_FESTIVALS.items():
        dates[name] = date(year, m, d)
    may_first = date(year, 5, 1)
    dates["母親節"] = may_first + timedelta(days=(6 - may_first.weekday()) % 7 + 7)  # 五月第二個星期日
    return dates


def check_names_match_table(dates: dict):
    table = {k for k in json.loads((WORK / "festivals.json").read_text(encoding="utf-8")) if not k.startswith("_")}
    missing, extra = table - set(dates), set(dates) - table
    if missing or extra:
        raise SystemExit(f"✗ 日期表與 festivals.json 對不上：缺 {sorted(missing)}、多 {sorted(extra)}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("list"); ls.add_argument("year", type=int)
    due = sub.add_parser("due"); due.add_argument("--days", type=int, default=3); due.add_argument("--today")
    args = ap.parse_args()

    if args.cmd == "list":
        dates = festival_dates(args.year)
        check_names_match_table(dates)
        for name, d in sorted(dates.items(), key=lambda kv: kv[1]):
            print(d.isoformat(), name)
        return

    today = date.fromisoformat(args.today) if args.today else datetime.now(TAIPEI).date()
    target = today + timedelta(days=args.days)
    dates = festival_dates(target.year)
    check_names_match_table(dates)
    hits = [(d, name) for name, d in sorted(dates.items()) if d == target]
    for d, name in hits:
        print(d.isoformat(), name)
    if not hits:
        # 明確印出來：排程要能分辨「今天沒節慶」與「指令出錯所以沒輸出」，後者不能被當成前者安靜跳過
        print(f"沒有節慶 {target.isoformat()}")


if __name__ == "__main__":
    main()
