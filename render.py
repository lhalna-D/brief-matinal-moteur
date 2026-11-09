#!/usr/bin/env python3
"""Assemble le Brief matinal (HTML -> PDF via Chromium/Playwright).

Usage : python3 render.py data.json content.json sortie.pdf
  data.json    : produit par fetch_data.py (chiffres de marché)
  content.json : texte rédigé du jour (voir CONTENT_SCHEMA.md)
"""
import json, sys, html, datetime as dt

E = html.escape

# ---------- formats français ----------
def fnum(x, dec=2):
    if x is None:
        return "–"
    s = f"{x:,.{dec}f}".replace(",", " ").replace(".", ",")
    return s

def fpct(x, dec=1):
    if x is None:
        return '<span class="mut">–</span>'
    cls = "pos" if x > 0.005 else ("neg" if x < -0.005 else "mut")
    sign = "+" if x > 0 else ("−" if x < 0 else "")
    return f'<span class="{cls}">{sign}{fnum(abs(x), dec)} %</span>'

def fbp(x):
    if x is None:
        return "–"
    cls = "pos" if x > 0.05 else ("neg" if x < -0.05 else "mut")
    sign = "+" if x > 0 else ("−" if x < 0 else "")
    return f'<span class="{cls}">{sign}{fnum(abs(x), 1)}</span>'

# Pour les taux, une hausse n'est ni « bonne » ni « mauvaise » : couleur neutre.
def fbp_neutral(x):
    if x is None:
        return "–"
    sign = "+" if x > 0 else ("−" if x < 0 else "")
    return f"{sign}{fnum(abs(x), 1)}"

# ---------- graphiques SVG ----------
BLUE, RED, GRID, AXIS, MUTED, INK2 = "#2a78d6", "#e34948", "#e1e0d9", "#c3c2b7", "#898781", "#52514e"

def svg_diverging(rows, title, width=330, row_h=18):
    """rows: [(libellé, valeur %)] barres horizontales, 0 au centre."""
    rows = [r for r in rows if r[1] is not None]
    lab_w, val_w = 108, 44
    plot_w = width - lab_w - val_w
    m = max(abs(v) for _, v in rows) or 1
    m = m * 1.45  # marge pour les étiquettes de valeur
    h = row_h * len(rows) + 22
    x0 = lab_w + plot_w / 2
    out = [f'<svg viewBox="0 0 {width} {h}" width="100%" role="img" aria-label="{E(title)}" class="chart">']
    out.append(f'<line x1="{x0}" y1="4" x2="{x0}" y2="{h-16}" stroke="{AXIS}" stroke-width="1"/>')
    for i, (lab, v) in enumerate(rows):
        y = 6 + i * row_h
        w = abs(v) / m * (plot_w / 2)
        x = x0 if v >= 0 else x0 - w
        col = BLUE if v >= 0 else RED
        out.append(f'<text x="{lab_w-6}" y="{y+row_h/2+3}" text-anchor="end" class="cl">{E(lab)}</text>')
        out.append(f'<rect x="{x:.1f}" y="{y+3}" width="{max(w,1):.1f}" height="{row_h-7}" rx="2" fill="{col}"/>')
        sign = "+" if v > 0 else ("−" if v < 0 else "")
        tx = x0 + w + 4 if v >= 0 else x0 - w - 4
        anchor = "start" if v >= 0 else "end"
        out.append(f'<text x="{tx:.1f}" y="{y+row_h/2+3}" text-anchor="{anchor}" class="cv">{sign}{fnum(abs(v),1)}%</text>')
    out.append(f'<text x="{x0}" y="{h-4}" text-anchor="middle" class="ca">0</text>')
    out.append("</svg>")
    return "".join(out)

def svg_bars(rows, title, highlight=(), width=330, row_h=15, unit="%"):
    """rows: [(libellé, valeur)] barres horizontales depuis 0, triées."""
    lab_w, val_w = 82, 40
    plot_w = width - lab_w - val_w
    m = max(v for _, v in rows) * 1.02 or 1
    h = row_h * len(rows) + 22
    out = [f'<svg viewBox="0 0 {width} {h}" width="100%" role="img" aria-label="{E(title)}" class="chart">']
    step = 1 if m <= 6 else 2
    t = 0
    while t <= m:
        gx = lab_w + t / m * plot_w
        out.append(f'<line x1="{gx:.1f}" y1="4" x2="{gx:.1f}" y2="{h-16}" stroke="{GRID if t else AXIS}" stroke-width="1"/>')
        out.append(f'<text x="{gx:.1f}" y="{h-4}" text-anchor="middle" class="ca">{t}{unit}</text>')
        t += step
    for i, (lab, v) in enumerate(rows):
        y = 6 + i * row_h
        w = v / m * plot_w
        col = "#184f95" if lab in highlight else "#86b6ef"
        weight = ' font-weight="700"' if lab in highlight else ""
        out.append(f'<text x="{lab_w-6}" y="{y+row_h/2+3}" text-anchor="end" class="cl"{weight}>{E(lab)}</text>')
        out.append(f'<rect x="{lab_w}" y="{y+3}" width="{max(w,1):.1f}" height="{row_h-7}" rx="2" fill="{col}"/>')
        out.append(f'<text x="{lab_w+w+4:.1f}" y="{y+row_h/2+3}" class="cv"{weight}>{fnum(v,2)}</text>')
    out.append("</svg>")
    return "".join(out)

# ---------- blocs HTML ----------
def quote_table(quotes, group, cols=("last", "d1", "w1", "ytd"), stale_days=5, ref_date=None):
    rows = []
    for q in quotes:
        if q.get("group") not in (group if isinstance(group, tuple) else (group,)) or "error" in q:
            continue
        stale = ""
        if ref_date:
            age = (ref_date - dt.date.fromisoformat(q["date"])).days
            if age > stale_days:
                stale = f' <span class="stale">au {dt.date.fromisoformat(q["date"]).strftime("%d/%m")}</span>'
        rows.append(f'<tr><td>{E(q["label"])}{stale}</td><td class="n">{fnum(q["last"], q["dec"])}</td>'
                    f'<td class="n">{fpct(q["d1"])}</td><td class="n">{fpct(q["w1"])}</td><td class="n">{fpct(q["ytd"])}</td></tr>')
    if not rows:
        return ""
    return ('<table class="q"><thead><tr><th></th><th class="n">Dernier</th><th class="n">1 j</th>'
            '<th class="n">1 sem.</th><th class="n">Depuis 1/1</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table>")

def bullets(items):
    return "<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>"

def news(items):
    out = []
    for it in items:
        tag = f'<span class="tag">{E(it["theme"])}</span> ' if it.get("theme") else ""
        out.append(f'<div class="news">{tag}<b>{E(it["titre"])}</b> — {it["texte"]}</div>')
    return "".join(out)

def ft_block(items):
    if not items:
        return ""
    lis = "".join(f'<li><a href="{E(it["url"])}"><b>{E(it["titre"])}</b></a> — {it["pourquoi"]}</li>' for it in items)
    return f'<div class="ft avoid"><h2>À lire dans le FT</h2><ul>{lis}</ul></div>'

CSS = """
@page { size: A4; margin: 11mm 12mm 12mm 12mm; }
* { box-sizing: border-box; }
body { font-family: 'Carlito', 'Liberation Sans', sans-serif; font-size: 9pt; line-height: 1.38; color: #0b0b0b; margin: 0; background: #fff; }
.mast { display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 2px solid #0d366b; padding-bottom: 5px; margin-bottom: 8px; }
.mast h1 { font-size: 20pt; margin: 0; color: #0d366b; letter-spacing: -0.3px; }
.mast .d { text-align: right; color: #52514e; font-size: 8.5pt; }
.mast .d b { color: #0b0b0b; font-size: 10.5pt; }
h2 { font-size: 10.5pt; color: #0d366b; margin: 10px 0 4px; padding-bottom: 2px; border-bottom: 1px solid #e1e0d9; text-transform: uppercase; letter-spacing: 0.4px; }
h3 { font-size: 8.8pt; margin: 6px 0 3px; color: #0b0b0b; }
.ess { background: #eef4fc; border-left: 3px solid #2a78d6; padding: 6px 10px 6px 8px; border-radius: 3px; }
.ess h2 { border: 0; margin: 0 0 3px; }
.ess ul { margin: 0; padding-left: 15px; } .ess li { margin: 2px 0; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.grid2 > div { min-width: 0; }
table.q { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
table.q th { font-weight: 400; color: #898781; font-size: 7.4pt; text-align: left; border-bottom: 1px solid #c3c2b7; padding: 1px 3px; }
table.q td { padding: 1.6px 3px; border-bottom: 1px solid #f0efec; white-space: nowrap; }
table.q td:first-child { white-space: normal; }
table.cbt td:nth-child(2) { white-space: nowrap !important; }
.n { text-align: right; }
.pos { color: #0a7a0a; } .neg { color: #c62f2f; } .mut { color: #898781; }
.stale { color: #b06a00; font-size: 6.8pt; }
.com { color: #2b2b29; margin: 4px 0 0; }
.chart text.cl { font-size: 7.6px; fill: #52514e; } .chart text.cv { font-size: 7.4px; fill: #0b0b0b; font-variant-numeric: tabular-nums; }
.chart text.ca { font-size: 6.8px; fill: #898781; }
.cap { font-size: 7.4pt; color: #52514e; margin: 2px 0 1px; font-weight: 700; }
.news { margin: 3px 0 4px; }
.tag { display: inline-block; font-size: 6.8pt; font-weight: 700; color: #0d366b; background: #e4eefb; padding: 0 4px; border-radius: 2px; text-transform: uppercase; letter-spacing: 0.3px; }
.notion { background: #f7f5ee; border: 1px solid #e6dfc8; border-radius: 4px; padding: 6px 10px; margin-top: 8px; }
.notion h2 { border: 0; margin: 0 0 2px; color: #7a5a00; }
.agenda td { vertical-align: top; white-space: normal !important; }
.agenda td:first-child { white-space: nowrap !important; font-weight: 700; width: 62px; }
.src { font-size: 6.6pt; color: #898781; margin-top: 8px; border-top: 1px solid #e1e0d9; padding-top: 3px; line-height: 1.3; }
.src a { color: #898781; text-decoration: none; }
.avoid { break-inside: avoid; }
.ft { background: #fff1e5; border-left: 3px solid #990f3d; padding: 4px 10px 5px 8px; border-radius: 3px; margin-top: 8px; }
.ft h2 { border: 0; margin: 0 0 2px; color: #990f3d; }
.ft ul { margin: 0; padding-left: 15px; } .ft li { margin: 2px 0; } .ft a { color: #0b0b0b; text-decoration: none; }
.pb { break-before: page; }
i, em { font-style: normal; color: #52514e; }
"""

def build(data, c):
    quotes = data["quotes"]
    ref = dt.date.fromisoformat(c["date"])
    by = {q["label"]: q for q in quotes if "error" not in q}

    # graphique 1 : perf hebdo des indices
    order = ["CAC 40", "Euro Stoxx 50", "DAX", "FTSE 100", "SMI (Suisse)", "S&P 500", "Nasdaq Composite",
             "Dow Jones", "Nikkei 225", "Hang Seng", "Shanghai Composite", "MSCI World (ETF URTH, $)"]
    short = {"MSCI World (ETF URTH, $)": "MSCI World", "SMI (Suisse)": "SMI", "Nasdaq Composite": "Nasdaq",
             "Shanghai Composite": "Shanghai"}
    perf_rows = [(short.get(k, k), by[k]["w1"]) for k in order if k in by]
    chart_eq = svg_diverging(perf_rows, "Performance des indices sur une semaine")

    # graphique 2 : taux 10 ans
    bonds = data.get("bonds", {})
    brow = sorted([(k, v["y"]) for k, v in bonds.items() if isinstance(v, dict) and "y" in v], key=lambda r: -r[1])
    chart_b = svg_bars(brow, "Taux souverains à 10 ans", highlight=("France", "Allemagne"))
    btab = "".join(f'<tr><td>{E(k)}</td><td class="n">{fnum(v["y"],2)} %</td><td class="n">{fbp_neutral(v.get("d1_bp"))}</td></tr>'
                   for k, v in sorted(bonds.items(), key=lambda kv: -kv[1]["y"]) if isinstance(v, dict) and "y" in v)
    spread = ""
    if "France" in bonds and "Allemagne" in bonds:
        s = (bonds["France"]["y"] - bonds["Allemagne"]["y"]) * 100
        spread_it = (bonds["Italie"]["y"] - bonds["Allemagne"]["y"]) * 100 if "Italie" in bonds else None
        fr_it = (bonds["France"]["y"] - bonds["Italie"]["y"]) * 100 if "Italie" in bonds else None
        spread = (f'<tr><td><b>Écart OAT – Bund</b></td><td class="n"><b>{fnum(s,0)} pb</b></td><td></td></tr>'
                  + (f'<tr><td>Écart BTP (Italie) – Bund</td><td class="n">{fnum(spread_it,0)} pb</td><td></td></tr>' if spread_it is not None else "")
                  )

    cb = "".join(f'<tr><td><b>{E(r["banque"])}</b></td><td class="n">{E(r["taux"])}</td><td>{r["derniere"]}</td>'
                 f'<td>{E(r["prochaine"])}</td><td>{r["tendance"]}</td></tr>' for r in c["banques_centrales"])
    ag = "".join(f'<tr><td>{E(a["jour"])}</td><td>{a["evenement"]}</td></tr>' for a in c["agenda"])

    body = f"""
<div class="mast"><h1>Brief Matinal</h1>
<div class="d"><b>{E(c["date_label"])}</b><br>{E(c["data_note"])}</div></div>

<div class="ess"><h2>L'essentiel en 30 secondes</h2>{bullets(c["essentiel"])}</div>

<h2>Marchés actions</h2>
<div class="grid2">
 <div>{quote_table(quotes, "actions", ref_date=ref)}<p class="com">{c["actions_commentaire"]}</p></div>
 <div><div class="cap">Performance sur une semaine</div>{chart_eq}</div>
</div>

<div class="avoid"><h2>Marché des taux · emprunts d'État à 10 ans</h2>
<div class="grid2">
 <div><div class="cap">Rendement à 10 ans (%) — France et Allemagne en foncé</div>{chart_b}</div>
 <div><table class="q"><thead><tr><th></th><th class="n">Taux</th><th class="n">Var. 1 j (pb)</th></tr></thead>
 <tbody>{btab}{spread}</tbody></table></div>
</div>
</div><p class="com">{c["taux_commentaire"]}</p>

<div class="grid2 avoid">
 <div><h2>Devises</h2>{quote_table(quotes, "devises", ref_date=ref)}
      <h2>Volatilité &amp; crypto</h2>{quote_table(quotes, ("volatilite", "crypto"), ref_date=ref)}</div>
 <div><h2>Matières premières</h2>{quote_table(quotes, "matieres", ref_date=ref, stale_days=6)}
      <p class="com">{c["autres_commentaire"]}</p></div>
</div>

<div class="avoid"><h2>Banques centrales</h2>
<table class="q agenda cbt"><thead><tr><th>Banque</th><th class="n">Taux</th><th>Dernière décision</th><th>Prochaine</th><th>Tendance</th></tr></thead>
<tbody>{cb}</tbody></table></div>

<div class="avoid"><h2>Agenda</h2><table class="q agenda"><tbody>{ag}</tbody></table></div>

<h2>Monde</h2>{news(c["monde"])}
<h2>France</h2>{news(c["france"])}
{ft_block(c.get("ft", []))}
<h2>Patrimoine · fiscalité · épargne · immobilier · retraite</h2>{news(c["patrimoine"])}

<div class="notion avoid"><h2>Notion du jour · {E(c["notion"]["titre"])}</h2>{c["notion"]["texte"]}</div>

<div class="src"><b>Sources :</b> {" · ".join(c["sources"])}<br>
Données de marché : Yahoo Finance (MSCI World approché par l'ETF iShares URTH, en dollars), Trading Economics (taux 10 ans), BCE (taux directeurs).
Variations calculées sur les dernières clôtures disponibles. Document d'information générale, ne constitue pas un conseil en investissement.</div>
"""
    return f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Brief Matinal {E(c["date"])}</title><style>{CSS}</style></head><body>{body}</body></html>'

def main():
    data = json.load(open(sys.argv[1]))
    content = json.load(open(sys.argv[2]))
    out_pdf = sys.argv[3]
    page = build(data, content)
    html_path = out_pdf.rsplit(".", 1)[0] + ".html"
    open(html_path, "w").write(page)
    import subprocess, os
    here = os.path.dirname(os.path.abspath(__file__))
    subprocess.run(["node", os.path.join(here, "pdf.js"), html_path, out_pdf], check=True, cwd=here)

if __name__ == "__main__":
    main()
