# Brief Matinal — procédure quotidienne (version Claude)

Objectif : chaque jour ouvré (lundi–vendredi, **y compris les jours fériés français**), produire un PDF
court (cible : **3 pages A4**, 4 maximum) lisible en 5–10 minutes avant de partir, et le déposer dans le
dossier Google Drive « Brief Matinal » sous le nom **`Brief Matinal - AAAA-MM-JJ.pdf`** (date du jour, heure de Paris).

Lecteur : étudiant / futur professionnel de la gestion de patrimoine et de la banque privée.
Ton : factuel, concis, **pédagogique** — expliquer en une phrase « pourquoi c'est important pour un client ».
Langue : français. Couverture : France, zone euro, États-Unis en priorité ; Royaume-Uni, Japon, Chine, Suisse en second plan.

## Étapes

Travailler à la racine de ce dépôt (cloné en lecture seule).

1. **Date du jour** : `TZ=Europe/Paris date +%F` → `JOUR`. Libellé du type « Lundi 9 novembre 2026 ».
2. **Données de marché** : `python3 fetch_data.py data.json` (Yahoo Finance, Trading Economics, BCE).
   Vérifier la sortie : toute ligne `ERREUR` ou donnée manifestement aberrante doit être signalée dans le texte,
   jamais inventée. Le tableau marque automatiquement les cotations de plus de 5 jours (« au JJ/MM »).
3. **Recherches web** (WebSearch, privilégier `extended` pour l'actualité des dernières 24 h) — couvrir :
   - Explications des mouvements de marché de la veille (Europe, Wall Street) et de la nuit en Asie.
   - Banques centrales : Fed, BCE, BoE, BoJ, BNS, PBoC — taux actuel, dernière décision (date, vote), prochaine réunion, tendance.
     Contrôler le taux BCE avec `data.json` (champ `ecb`). Mettre à jour uniquement si une décision ou un discours a changé la donne.
   - Agenda du jour et des jours suivants (publications macro avec l'heure de Paris, résultats d'entreprises majeurs, réunions).
   - Faits marquants monde (3–4) et France (2–3) : politique, économie, géopolitique ayant un effet sur les marchés ou l'épargne.
   - Patrimoine (4–5 brèves) : fiscalité (PLF/PLFSS, IFI, flat tax, successions, assurance-vie, PER), épargne réglementée
     (Livret A, LEP, PEL), crédit immobilier (baromètres courtiers), placements (fonds euros, SCPI, collecte), retraites.
     Privilégier ce qui a **bougé** ; sinon rappeler brièvement les niveaux en vigueur.
   - Toujours dater les faits ; croiser au moins deux sources pour un chiffre important ; écarter les pages périmées.
4. **Rédiger `content.json`** (même structure que `exemple_content_2026-11-08.json`) :
   - `date` (= JOUR), `date_label`, `data_note` (ex. « Clôtures du vendredi 6 nov. · devises au 9 nov. 7h »).
   - `essentiel` : 4–5 puces, la dernière = « À surveiller aujourd'hui ».
   - `actions_commentaire`, `taux_commentaire`, `autres_commentaire` : 2–4 phrases chacun, en s'appuyant sur les chiffres de `data.json`.
   - `banques_centrales` (6 lignes), `agenda` (3–6 lignes), `monde`, `france`, `patrimoine` (objets `theme`/`titre`/`texte`).
   - `notion` : traiter **la notion donnée par `python3 notion_du_jour.py JOUR`** (une par jour ouvré, liste `notions.txt`),
     en la reliant si possible à l'actualité, en 150–220 mots : définition, chiffres clés, « pourquoi c'est important pour un client ».
   - `sources` : liens HTML `<a href='…'>Nom</a>` vers les articles utilisés.
   - HTML autorisé dans les textes : `<b>`, `<i>`, `<sup>`, `<p>`. Échapper les guillemets JSON.
5. **PDF** : `python3 render.py data.json content.json "out/Brief Matinal - JOUR.pdf"` (créer `out/`).
   Contrôle : `pdfinfo` → 3 pages idéalement, 4 maximum (sinon raccourcir les textes et relancer).
   Convertir la page 1 en PNG (`pdftoppm -r 60 -png -f 1 -l 1`) et la regarder : pas de chevauchement ni de colonne coupée.
6. **Dépôt Drive** : `python3 upload.py "out/Brief Matinal - JOUR.pdf"` avec les variables `BRIEF_UPLOAD_URL` et
   `BRIEF_UPLOAD_SECRET` fournies dans le message de la tâche planifiée. La réponse doit contenir `"ok":true`.
   En cas d'échec réseau, réessayer 2 fois (30 s d'intervalle). Un nouveau dépôt le même jour remplace l'ancien fichier.
7. Terminer par un résumé de 3 lignes : nom du fichier, lien Drive, éventuelles données manquantes.

## Règles

- Ne jamais inventer un chiffre : si une donnée manque, l'écrire (« non disponible ce matin »).
- Les données de `data.json` font foi pour les cours ; les recherches servent à expliquer.
- Week-ends et jours sans séance : utiliser la dernière clôture et le dire dans `data_note`.
- Rester court : c'est un brief, pas un rapport.
- Sobriété : viser 8 à 10 recherches web au total (lancées en parallèle par lots), ne regarder que la page 1 du PDF,
  pas de relectures inutiles de fichiers. Le brief doit être prêt en 10–15 minutes.
