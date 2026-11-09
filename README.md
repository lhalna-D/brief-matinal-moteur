# Brief Matinal — moteur

Scripts du Brief Matinal (PDF quotidien de marchés et de patrimoine) générés chaque jour ouvré par une tâche
planifiée Claude Code, dans une session neuve qui clone ce dépôt public en lecture seule.

- `fetch_data.py` : cours (Yahoo Finance), taux 10 ans (Trading Economics), taux BCE
- `render.py` + `pdf.js` : mise en page HTML → PDF (Chromium)
- `upload.py` + `apps_script_depot_drive.gs` : dépôt dans Google Drive via une Apps Script
- `notions.txt` + `notion_du_jour.py` : notion pédagogique du jour
- `INSTRUCTIONS.md` : procédure suivie chaque matin

Aucun secret n'est stocké ici : l'URL de l'Apps Script et son mot de passe sont fournis par la tâche planifiée.
