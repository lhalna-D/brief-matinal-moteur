#!/usr/bin/env python3
"""Dépose le PDF dans le dossier Drive « Brief Matinal » via l'Apps Script.

Usage : BRIEF_UPLOAD_URL=... BRIEF_UPLOAD_SECRET=... python3 upload.py "Brief Matinal - AAAA-MM-JJ.pdf"
"""
import base64, json, os, subprocess, sys, tempfile

path = sys.argv[1]
url = os.environ["BRIEF_UPLOAD_URL"]
payload = {"secret": os.environ["BRIEF_UPLOAD_SECRET"], "nom": os.path.basename(path),
           "pdf_base64": base64.b64encode(open(path, "rb").read()).decode()}
with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
    json.dump(payload, f)
# Apps Script répond par une redirection 302 vers script.googleusercontent.com (GET) : -L la suit.
r = subprocess.run(["curl", "-sS", "-L", "-m", "120", "-H", "Content-Type: application/json",
                    "--data-binary", "@" + f.name, url], capture_output=True, text=True)
os.unlink(f.name)
print(r.stdout or r.stderr)
try:
    res = json.loads(r.stdout)
except Exception:
    sys.exit("Échec du dépôt : réponse inattendue")
sys.exit(0 if res.get("ok") else 1)
