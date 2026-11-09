#!/usr/bin/env python3
"""Affiche la notion du jour : on avance d'une notion par jour ouvré depuis le 2026-11-09 (qui a eu la n°2)."""
import datetime as dt, sys
start = dt.date(2026, 11, 9)
today = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date.today()
notions = [l.strip() for l in open(__file__.rsplit("/", 1)[0] + "/notions.txt", encoding="utf-8") if l.strip()]
n = 0
d = start
while d < today:
    d += dt.timedelta(days=1)
    if d.weekday() < 5:
        n += 1
print(notions[(1 + n) % len(notions)])
