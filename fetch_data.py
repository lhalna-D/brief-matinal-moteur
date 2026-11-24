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

# Taux souverains à 10 ans.
# Source principale : pages pays de Trading Economics (phrase datée de la meta description).
# Secours : Boursorama (tableau « 10 ans » de /bourse/taux/), parfois en retard de plusieurs jours.
# (Le tableau https://tradingeconomics.com/bonds est désormais chargé en JavaScript : inutilisable.)
BONDS = {  # pays -> (code ISO Boursorama, slug Trading Economics)
    "États-Unis": ("USA", "united-states"), "Allemagne": ("DEU", "germany"), "France": ("FRA", "france"),
    "Italie": ("ITA", "italy"), "Espagne": ("ESP", "spain"), "Royaume-Uni": ("GBR", "united-kingdom"),
    "Japon": ("JPN", "japan"), "Suisse": ("CHE", "switzerland"), "Chine": ("CHN", "china"),
}

def _num(x):
    return float(x.replace("\u202f", "").replace(" ", "").replace(",", "."))

def bonds_boursorama():
    h = get("https://www.boursorama.com/bourse/taux/")
    iso = {v[0]: k for k, v in BONDS.items()}
    out = {}
    for code, y, bp in re.findall(r'title="([A-Z]{3}) BENCHMARK 10A"[^>]*>\s*([\-\d,]+)%</a>\s*</td>\s*<td[^>]*>\s*([\-+\d,]+) BP', h):
        if code in iso and iso[code] not in out:
            out[iso[code]] = dict(y=_num(y), d1_bp=_num(bp), date="", src="Boursorama")
    return out

def bond_te(slug):
    h = get(f"https://tradingeconomics.com/{slug}/government-bond-yield")
    m = re.search(r'name="description" content="([^"]+)"', h) or re.search(r'id="metaDesc"[^>]*content="([^"]+)"', h)
    if not m:
        return None
    d = m.group(1)
    y = re.search(r'Yield (?:\w+ ){0,3}?(?:to |at )([\d.]+)%', d)
    if not y:
        return None
    chg = re.search(r'a ([\d.]+) percentage points? (increase|decrease)', d)
    bp = None
    if chg:
        bp = float(chg.group(1)) * 100 * (1 if chg.group(2) == "increase" else -1)
    elif "held steady" in d:
        bp = 0.0
    date = re.search(r' on ([A-Z][a-z]+ \d{1,2}, \d{4})', d)
    return dict(y=float(y.group(1)), d1_bp=None if bp is None else round(bp, 1), date=date.group(1) if date else "", src="Trading Economics")

def bonds():
    """Source principale : pages pays Trading Economics (datées, cohérentes avec Yahoo/FRED).
    Secours : Boursorama (parfois en retard de plusieurs jours, d'où la mention « secours »)."""
    out = {}
    def one(item):
        pays, (_, slug) = item
        try:
            return pays, bond_te(slug)
        except Exception as e:
            print("Trading Economics indisponible pour", pays, ":", str(e)[:120])
            return pays, None
    with ThreadPoolExecutor(3) as ex:
        for pays, r in ex.map(one, BONDS.items()):
            if r:
                out[pays] = r
    if len(out) < len(BONDS):
        try:
            for pays, r in bonds_boursorama().items():
                if pays not in out:
                    r["src"] = "Boursorama (secours, peut être en retard)"
                    out[pays] = r
        except Exception as e:
            print("Boursorama indisponible :", str(e)[:120])
    manquants = [p for p in BONDS if p not in out]
    if manquants:
        print("ATTENTION taux 10 ans manquants :", ", ".join(manquants))
    return {p: out[p] for p in BONDS if p in out}

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
