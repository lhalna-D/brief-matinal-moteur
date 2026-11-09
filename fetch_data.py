#!/usr/bin/env python3
"""Collecte les données de marché pour le Brief matinal -> data.json

Sources : Yahoo Finance (indices, devises, matières premières, crypto, volatilité),
Trading Economics (taux souverains 10 ans), BCE (taux directeurs BCE).
Usage : python3 fetch_data.py [sortie.json]
"""
import json, re, subprocess, sys, time, datetime as dt
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"

def get(url, timeout=25, ua=UA):
    r = subprocess.run(["curl", "-sS", "-L", "-m", str(timeout), "-A", ua, url],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r.stdout

# (groupe, libellé, ticker Yahoo, décimales)
YAHOO = [
    ("actions", "CAC 40", "^FCHI", 0),
    ("actions", "Euro Stoxx 50", "^STOXX50E", 0),
    ("actions", "DAX", "^GDAXI", 0),
    ("actions", "FTSE 100", "^FTSE", 0),
    ("actions", "SMI (Suisse)", "^SSMI", 0),
    ("actions", "S&P 500", "^GSPC", 0),
    ("actions", "Nasdaq Composite", "^IXIC", 0),
    ("actions", "Dow Jones", "^DJI", 0),
    ("actions", "Nikkei 225", "^N225", 0),
    ("actions", "Hang Seng", "^HSI", 0),
    ("actions", "Shanghai Composite", "000001.SS", 0),
    ("actions", "MSCI World (ETF URTH, $)", "URTH", 2),
    ("volatilite", "VIX (S&P 500)", "^VIX", 2),
    ("devises", "EUR/USD", "EURUSD=X", 4),
    ("devises", "EUR/GBP", "EURGBP=X", 4),
    ("devises", "EUR/CHF", "EURCHF=X", 4),
    ("devises", "USD/JPY", "JPY=X", 2),
    ("devises", "USD/CNY", "CNY=X", 4),
    ("devises", "Dollar Index (DXY)", "DX-Y.NYB", 2),
    ("matieres", "Brent ($/baril)", "BZ=F", 2),
    ("matieres", "WTI ($/baril)", "CL=F", 2),
    ("matieres", "Gaz TTF (€/MWh)", "TTF=F", 2),
    ("matieres", "Or ($/oz)", "GC=F", 0),
    ("matieres", "Argent ($/oz)", "SI=F", 2),
    ("matieres", "Cuivre ($/lb)", "HG=F", 3),
    ("crypto", "Bitcoin ($)", "BTC-USD", 0),
    ("crypto", "Bitcoin (€)", "BTC-EUR", 0),
]

def yahoo(item):
    group, label, tk, dec = item
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{tk.replace('^', '%5E')}?range=1y&interval=1d"
    try:
        j = None
        for attempt in range(3):
            try:
                j = json.loads(get(url, ua="Mozilla/5.0"))["chart"]["result"][0]; break
            except Exception:
                if attempt == 2: raise
                time.sleep(2 * (attempt + 1))
        ts = j["timestamp"]; closes = j["indicators"]["quote"][0]["close"]
        pts = [(dt.datetime.fromtimestamp(t, dt.timezone.utc).date(), c) for t, c in zip(ts, closes) if c is not None]
        meta = j["meta"]
        last = meta.get("regularMarketPrice") or pts[-1][1]
        last_date = dt.datetime.fromtimestamp(meta["regularMarketTime"], dt.timezone.utc).date()
        # dernière clôture distincte avant la séance de last_date
        prev = [c for d, c in pts if d < last_date]
        prevc = prev[-1] if prev else None
        def perf(ref):
            return None if not ref else (last / ref - 1) * 100
        wk = [c for d, c in pts if d <= last_date - dt.timedelta(days=7)]
        ytd = [c for d, c in pts if d.year < last_date.year]
        return dict(group=group, label=label, ticker=tk, dec=dec, last=last,
                    date=str(last_date), d1=perf(prevc), w1=perf(wk[-1] if wk else None),
                    ytd=perf(ytd[-1] if ytd else None),
                    hist=[[str(d), round(c, 6)] for d, c in pts[-130:]])
    except Exception as e:
        return dict(group=group, label=label, ticker=tk, error=str(e)[:200])

BONDS = {"USGG10YR": "États-Unis", "GDBR10": "Allemagne", "GFRN10": "France",
         "GBTPGR10": "Italie", "GSPG10YR": "Espagne", "GUKG10": "Royaume-Uni",
         "GJGB10": "Japon", "GSWISS10": "Suisse", "GCNY10YR": "Chine"}

def bonds():
    h = get("https://tradingeconomics.com/bonds")
    out = {}
    for tr in re.findall(r'<tr data-symbol="(.*?)</tr>', h, re.S):
        sym = tr.split(":")[0]
        if sym not in BONDS or BONDS[sym] in out:
            continue
        p = re.search(r'id="p" class="datatable-item">\s*([\-\d\.]+)', tr)
        vals = re.findall(r'data-value="([\-\d\.]+)"', tr)
        date = re.search(r'id="date"[^>]*>\s*([^<]+?)\s*<', tr)
        if p:
            out[BONDS[sym]] = dict(y=float(p.group(1)), d1_bp=float(vals[0]) * 100 if vals else None,
                                   date=date.group(1) if date else "")
    return out

def ecb():
    res = {}
    for k, key in {"Taux de dépôt": "DFR", "Refi": "MRR_FR", "Prêt marginal": "MLFR"}.items():
        try:
            t = get(f"https://data-api.ecb.europa.eu/service/data/FM/D.U2.EUR.4F.KR.{key}.LEV?lastNObservations=1&format=csvdata")
            hdr, row = t.strip().splitlines()[:2]
            h = hdr.split(","); r = row.split(",")
            res[k] = dict(value=float(r[h.index("OBS_VALUE")]), date=r[h.index("TIME_PERIOD")])
        except Exception as e:
            res[k] = dict(error=str(e)[:120])
    return res

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "data.json"
    with ThreadPoolExecutor(3) as ex:
        quotes = list(ex.map(yahoo, YAHOO))
    try:
        b = bonds()
    except Exception as e:
        b = {"error": str(e)[:200]}
    data = dict(generated=dt.datetime.now(dt.timezone.utc).isoformat(), quotes=quotes, bonds=b, ecb=ecb())
    json.dump(data, open(out, "w"), ensure_ascii=False, indent=1)
    for q in quotes:
        if "error" in q:
            print("ERREUR", q["label"], q["error"])
        else:
            print(f'{q["label"]:28} {q["last"]:>12.{q["dec"]}f}  1j {q["d1"] or 0:+6.2f}%  1s {q["w1"] or 0:+6.2f}%  ytd {q["ytd"] or 0:+6.2f}%  {q["date"]}')
    print(json.dumps(b, ensure_ascii=False))
    print(json.dumps(data["ecb"], ensure_ascii=False))

if __name__ == "__main__":
    main()
