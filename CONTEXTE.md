# Brief Matinal — contexte du projet

> Fichier à lire en premier dans une nouvelle conversation avec Claude pour reprendre le projet.
> Dernière mise à jour : 24 novembre 2026.

## Objectif

Un PDF court (3 pages A4, lisible en 5–10 min) généré **chaque jour ouvré** (lundi–vendredi, jours fériés inclus)
et déposé dans le dossier Google Drive **« Brief Matinal »** sous le nom **`Brief Matinal - AAAA-MM-JJ.pdf`**.

Lecteur : étudiant à SKEMA qui se destine à la gestion de patrimoine / banque privée.
Ton : factuel, concis, **pédagogique** (« pourquoi c'est important pour un client »). Langue : français.
Couverture : France, zone euro, États-Unis en priorité ; Royaume-Uni, Japon, Chine, Suisse en second plan.

## Contenu du PDF

1. **L'essentiel en 30 secondes** (4–5 puces, la dernière = « À surveiller aujourd'hui »)
2. **Marchés actions** : CAC 40, Euro Stoxx 50, DAX, FTSE 100, SMI, S&P 500, Nasdaq, Dow Jones, Nikkei, Hang Seng,
   Shanghai, MSCI World (approché par l'ETF URTH en $) — variations 1 j / 1 sem. / depuis le 1er janvier + graphique hebdo
3. **Taux à 10 ans** (US, Allemagne, France, Italie, Espagne, R-U, Japon, Suisse, Chine) + écarts OAT–Bund et BTP–Bund
4. **Devises, matières premières** (Brent, WTI, gaz TTF, or, argent, cuivre), **volatilité** (VIX) et **bitcoin**
5. **Banques centrales** : Fed, BCE, BoE, BoJ, BNS, PBoC — taux, dernière décision, prochaine réunion, tendance
6. **Agenda** de la semaine
7. **Monde** (3–4 faits) et **France** (2–3 faits)
8. **À lire dans le FT** : 3–5 sujets du jour avec un lien de recherche ft.com (l'utilisateur lit avec son accès SKEMA)
9. **Patrimoine** : fiscalité (PLF/PLFSS, IFI, flat tax, successions, assurance-vie, PER), épargne réglementée,
   crédit immobilier, placements (fonds euros, SCPI), retraites
10. **Notion du jour** : une notion pédagogique par jour ouvré (liste `notions.txt`, choisie par `notion_du_jour.py`)
11. **Sources**

## Fonctionnement

- **Tâche planifiée Claude Code** « Brief Matinal (session neuve) » — id `trig_017Ud8gQFiQqMkiHUA9aLYDQ`
  - Déclenchement : `CRON_TZ=Europe/Paris 47 6 * * 1-5` (6h47, PDF dans Drive vers 7h).
  - Chaque matin : **session neuve** (historique vide → consommation faible), modèle **Sonnet** (`claude-sonnet-5-5`).
  - La session clone ce dépôt public `lhalna-D/brief-matinal-moteur` en lecture seule et suit `INSTRUCTIONS.md`.
  - Notification push à la fin.
  - **L'URL de l'Apps Script et le mot de passe de dépôt sont dans le texte de la tâche planifiée**, jamais dans ce dépôt public.
- **Dépôt dans Drive** : via une **Google Apps Script** (application Web, exécutée au nom de l'utilisateur), code dans
  `apps_script_depot_drive.gs`. Elle accepte un PDF en base64 + mot de passe, et remplace le fichier du jour s'il existe.
  Dossier Drive « Brief Matinal » : id `1zWPFUiZ5ypP6yg59nZfaOnbor7YDhlKx`.
  (Le connecteur Drive de Claude n'est pas utilisé : trop lourd pour envoyer un PDF chaque jour.)
- **Environnement cloud « Default »** : hôtes autorisés `query1/query2.finance.yahoo.com`, `tradingeconomics.com`,
  `data-api.ecb.europa.eu`, `fred.stlouisfed.org`, `www.boursorama.com`, `script.google.com`, `script.googleusercontent.com`.
  `www.ft.com` a été refusé par le service (et le FT bloque la recherche web) → d'où les liens de recherche FT.

## Fichiers de ce dépôt

| Fichier | Rôle |
|---|---|
| `INSTRUCTIONS.md` | Procédure suivie chaque matin par la tâche (étapes, règles, budget de recherches) |
| `fetch_data.py` | Cours Yahoo Finance, taux 10 ans, taux BCE → `data.json` |
| `render.py` + `pdf.js` | Mise en page HTML → PDF (Chromium/Playwright, police Carlito) |
| `upload.py` | Envoi du PDF à l'Apps Script (variables `BRIEF_UPLOAD_URL`, `BRIEF_UPLOAD_SECRET`) |
| `notions.txt` + `notion_du_jour.py` | 101 notions, une par jour ouvré depuis le 9 nov. 2026 |
| `exemple_content_2026-11-08.json` | Exemple de `content.json` (structure du texte rédigé chaque jour) |
| `apps_script_depot_drive.gs` | Code de l'Apps Script (mot de passe à définir dans la copie Google, pas ici) |

## Décisions et historique

- **8 nov. 2026** : premier brief de test validé (« Super le PDF »). Format court retenu, graphiques seulement s'ils apportent.
- La tâche tournait d'abord **dans la conversation de mise en place** → coût croissant (historique de plus en plus long).
  **9 nov.** : passage en **session neuve** + dépôt public + **Sonnet**. Contrôle visuel demandé sur **toutes les pages**.
- Les sessions neuves ne peuvent ni rattacher le dépôt **privé** `lhalna-D/Brief-Matinal`, ni écrire dans le dépôt public
  → la notion du jour vient d'une liste fixe au lieu d'un historique.
- **24 nov.** : la section taux 10 ans était vide depuis ~1 semaine (le tableau `tradingeconomics.com/bonds` est passé en
  JavaScript). Correctif : pages pays Trading Economics (source principale, datée, recoupée avec Yahoo `^TNX` et FRED),
  Boursorama en secours (attention : parfois en retard de plusieurs jours) + alerte `ATTENTION taux 10 ans manquants`.

## Autres éléments

- Le dépôt privé `lhalna-D/Brief-Matinal` contient sur `main` une **ancienne version** (GitHub Actions + Gemini, 7h30)
  écrite par l'utilisateur, à ne pas modifier. La branche `claude-brief` contient la première version Claude (obsolète).
  Si l'ancien workflow GitHub est encore actif, il peut produire un second PDF (« Brief Matinal AAAA-MM-JJ.pdf », sans tiret).
- Pistes non retenues : GitHub Actions + clé d'API Anthropic (payant à l'usage) ; résumé d'articles FT (non autorisé).

## Pour modifier le brief

- Contenu, ton, rubriques : éditer `INSTRUCTIONS.md` (et `render.py` pour la mise en page), pousser sur `main`.
  La tâche du lendemain prend automatiquement la nouvelle version.
- Horaire, modèle, texte de la tâche : modifier la tâche planifiée (`trig_017Ud8gQFiQqMkiHUA9aLYDQ`).
- Tester : `python3 fetch_data.py data.json && python3 render.py data.json exemple_content_2026-11-08.json out/t.pdf`.
