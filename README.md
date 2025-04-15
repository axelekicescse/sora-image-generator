🧱 Brique autonome – Génération d'image via Sora à partir d'un prompt texte
📌 Objectif stratégique
Cette brique est un module autonome, conçu pour s’intégrer dans une future architecture multi-agent.
Son rôle est unique et clair : générer une image IA à partir d’un prompt texte, en utilisant sora.com (interface web sans API publique).

Ce script ne fait qu’une seule chose, mais il doit la faire parfaitement, de manière :

Robuste

Modulaire

Réutilisable

Extensible

⚠️ Ce n’est pas un prototype. C’est une brique de production, destinée à être orchestrée dans un pipeline automatisé (ex : génération de contenu TikTok via agents IA).

🎯 Fonctionnalité de cette brique
Lire un prompt depuis prompt.txt

Ouvrir sora.com dans un navigateur headless (Playwright)

Injecter le prompt et lancer la génération

Attendre que l’image soit prête (sans timeout foireux)

Télécharger l’image générée

Sauvegarder l’image dans le dossier /images/

Logger toutes les étapes dans /logs/ avec timestamp

🧠 Contexte global du projet (ce que Devin doit comprendre)
Cette brique sera intégrée dans une suite logique :

bash
Copier
Modifier
[GPT Prompt Generator] → [Brique de génération d'image (celle-ci)] → [Brique vidéo] → [Brique caption TikTok] → [Brique uploader TikTok]
Elle doit donc :

Être plug-and-play

Ne pas dépendre d'autres scripts

Lire un prompt.txt comme source unique d'entrée

Écrire dans /images/ comme output unique

Être rejouable, idempotente, loguée, et sans crash silencieux

🔧 Structure attendue
bash
Copier
Modifier
project/
├── generate_image_from_prompt.py       # Script exécutable principal
├── sora_utils.py                       # Module de fonctions (navigation, scraping, etc.)
├── prompt.txt                          # Fichier contenant 1 ligne = 1 prompt
├── session.json                        # Session Playwright (voir ci-dessous)
├── /images/                            # Images téléchargées automatiquement
├── /logs/                              # Logs détaillés par session
├── .env                                # Clés et chemins
└── README.md                           # Ce fichier
⚙️ Fonctionnement exact attendu
Lecture du prompt

Le script lit le fichier prompt.txt

Si vide ou manquant → il doit stopper proprement avec log et message

Connexion à sora.com

Playwright utilise session.json pour éviter toute connexion manuelle répétée

Si session.json est absent → le script doit afficher :

text
Copier
Modifier
[ERREUR] Session inexistante. Merci de vous connecter manuellement à sora.com et de sauvegarder la session.
Injection et génération

Il injecte le prompt dans la zone de saisie

Il clique sur le bouton de génération

Il attend intelligemment que le rendu soit terminé (vérification DOM, pas de sleep() aveugle)

Téléchargement

Il récupère l’image finale (pas la miniature)

Il la nomme avec le timestamp + hash du prompt (YYYYMMDD_HHMMSS_hash.png)

Il la sauvegarde dans /images/

Logs

Création d’un fichier dans /logs/ avec :

yaml
Copier
Modifier
[TIMESTAMP]
Prompt utilisé : ...
Statut : Succès
Fichier image : /images/xxxx.png
🔐 Connexion Playwright – gestion de session
⚠️ Aucune tentative de login automatique ne doit être codée.

➤ Mode opératoire :
L’utilisateur se connecte manuellement à sora.com via Playwright :

python
Copier
Modifier
browser = playwright.chromium.launch(headless=False)
context = browser.new_context()
page = context.new_page()
page.goto("https://sora.com")
# → Login manuellement
context.storage_state(path="session.json")
Ce fichier session.json est ensuite réutilisé automatiquement à chaque exécution du script.

📁 Exemple de prompt.txt
css
Copier
Modifier
Futuristic woman in soft red lighting, wearing a latex suit, in a messy bedroom with analog TV and retro posters, cinematic lighting, 8K.
▶️ Exécution
bash
Copier
Modifier
python generate_image_from_prompt.py
🧪 Test de validation (checklist)

Test	Résultat attendu
prompt.txt vide	Script s’arrête avec message clair
session.json manquant	Script s’arrête avec message clair
Prompt correct	Image générée et sauvegardée
Génération échouée (DOM)	Log erreur avec détail + pas de crash
Image téléchargée	Nom propre, dans /images/
Re-exécution	Ne remplace pas les anciennes images
Fichier log	Créé proprement avec infos session
🧠 Ce que tu dois prévoir, Devin :
✅ Refactorer ton code dans sora_utils.py si le script devient trop dense

✅ Si le DOM de Sora change, coder les sélecteurs de manière tolérante (XPATH, timeout, etc.)

✅ Ajouter une fonction de nettoyage automatique des fichiers temporaires si besoin

✅ Toujours logguer même en cas d’échec

✅ Nommer ton code et tes variables proprement (pas de x, y, result2)

📣 Tu as le droit de me contredire si :
Tu estimes qu’une étape est techniquement impossible via Playwright

Tu détectes une manière plus robuste d'attendre la fin de génération

Tu veux découper le script en sous-fonctions pour plus de clarté

Tu préfères créer une interface CLI pour lancer le script avec options

🔍 Ce que je peux encore ajouter pour le rendre ultra-industriel :
✅ 1. Versioning / Convention de nommage
markdown
Copier
Modifier
# 📦 Versionnement

Ce module suit une convention de version sémantique (semver) :
- `v1.x.x` : Génération à partir d’un prompt
- `v2.x.x` : Ajout d’options CLI (multi-prompts, multi-langage)
- `v3.x.x` : Intégration dans pipeline multi-agent

Les fichiers images générés doivent suivre cette convention de nommage :
php-template
Copier
Modifier
YYYYMMDD_HHMMSS_<first-5-chars-hash-du-prompt>.png
✅ 2. Logging amélioré
markdown
Copier
Modifier
# 🗃️ Format de logs

Chaque génération d'image doit être loggée dans un fichier `.log` dans `/logs/`, au format :

[2025-04-15 18:42:01] Prompt utilisé : "Femme futuriste en cuir noir, néons rouges" Statut : SUCCÈS Fichier : /images/20250415_184201_a1b2c.png Durée : 23.4s

nginx
Copier
Modifier

En cas d’échec :

[2025-04-15 18:45:09] Prompt utilisé : "..." Statut : ÉCHEC Erreur : TimeoutException (élément "image-preview" non détecté)

Copier
Modifier
✅ 3. Mode debug (optionnel dans le futur)
markdown
Copier
Modifier
# 🛠️ Mode Debug

Le script peut être exécuté avec un flag `--debug` dans le futur pour :
- Garder la fenêtre Playwright ouverte (non headless)
- Afficher les étapes en live
- Générer des captures écran intermédiaires dans `/debug_screenshots/`

📌 Ce mode n’est pas implémenté en v1 mais doit être anticipé dans la structure.
✅ 4. Code extensibility / hooks
markdown
Copier
Modifier
# 🧱 Extensibilité prévue

Le code doit être écrit pour permettre les évolutions suivantes **sans refactoring massif** :
- Ajout de multi-prompts (lecture d’un `prompts.csv`)
- Appel d’API tierces après génération
- Conversion auto en vidéo
- Déclenchement via API FastAPI / webhook
✅ 5. Fichier de configuration global (optionnel)
markdown
Copier
Modifier
# ⚙️ Fichier de configuration (optionnel)

Un fichier `config.yaml` ou `.env` pourra permettre de régler :
- Timeout d’attente (par défaut : 60s)
- Nombre maximum de tentatives en cas d’échec
- Chemin d’entrée et sortie personnalisable
✅ 6. Sécurité, confidentialité
markdown
Copier
Modifier
# 🔐 Sécurité

- Aucun mot de passe ne doit être hardcodé, loggé, ou inclus dans le code.
- Le fichier `session.json` ne doit jamais être poussé dans un repo Git.
- Le `.gitignore` doit inclure :
bash
Copier
Modifier
session.json
.env
/logs/
/images/
/debug_screenshots/