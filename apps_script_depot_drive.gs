/**
 * Brief Matinal — réception des PDF dans Google Drive
 *
 * À coller dans un nouveau projet sur https://script.google.com
 * puis : Déployer > Nouveau déploiement > Type « Application Web »
 *        Exécuter en tant que : Moi
 *        Qui a accès : Tout le monde
 * Copier l'URL de déploiement (…/exec) et la transmettre à Claude.
 *
 * Le script ne fait qu'une chose : enregistrer un PDF reçu dans le dossier
 * « Brief Matinal », à condition que la requête porte le bon mot de passe.
 */

const DOSSIER_ID = '1zWPFUiZ5ypP6yg59nZfaOnbor7YDhlKx'; // dossier « Brief Matinal »
const MOT_DE_PASSE = 'CHANGEZ-MOI';                      // à définir dans votre copie Apps Script

function doPost(e) {
  const req = JSON.parse(e.postData.contents);
  if (req.secret !== MOT_DE_PASSE) {
    return reponse({ ok: false, erreur: 'non autorisé' });
  }
  if (!/^Brief Matinal - \d{4}-\d{2}-\d{2}\.pdf$/.test(req.nom)) {
    return reponse({ ok: false, erreur: 'nom de fichier invalide' });
  }
  const dossier = DriveApp.getFolderById(DOSSIER_ID);
  // remplace un éventuel fichier du même jour (relance)
  const existants = dossier.getFilesByName(req.nom);
  while (existants.hasNext()) existants.next().setTrashed(true);
  const blob = Utilities.newBlob(Utilities.base64Decode(req.pdf_base64), 'application/pdf', req.nom);
  const f = dossier.createFile(blob);
  return reponse({ ok: true, id: f.getId(), url: f.getUrl() });
}

function reponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
