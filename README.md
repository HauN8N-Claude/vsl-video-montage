# Montage vidéo VSL

Scripts Windows pour produire et contrôler le montage court du scénario A. Le pipeline utilise Python, Pillow, FFmpeg et FFprobe. FFmpeg doit disposer de libx264, du filtre ASS et de l'encodeur AAC.

Le dossier de travail reçoit la vidéo sous `01_SOURCES/VSL SOLAIRE V2.mp4`, le plan dans `04_ANALYSE_ET_TIMECODES/PLANS_MACHINE.json`, la transcription dans `03_TRANSCRIPTIONS/VSL_SOLAIRE_BRUT.json` et les repères vérifiés dans les fichiers `02_TRAVAIL/verification-A-*.json`. Le fichier local `local/phrases.json` contient les groupes de sous-titres par identifiant de séquence. Chaque groupe reprend les mots du plan, dans le même ordre.

Configure PowerShell à partir du dépôt. Utilise un dossier de travail dédié pour une nouvelle production.

```powershell
$env:VSL_PROJECT_DIR = 'C:/chemin/vers/dossier-de-travail'
$env:VSL_CAPTIONS_FILE = (Resolve-Path './local/phrases.json').Path
$env:VSL_BRAND = 'Nom de la marque'
python -m pip install -r requirements.txt
python scripts/produire_scenario_a.py
python scripts/controler_production_a.py
```

Si les exécutables ne figurent pas dans le PATH, renseigne leurs chemins absolus dans `VSL_FFMPEG` et `VSL_FFPROBE`. Le contrôle utilise des instants de capture adaptés au montage A d'environ 90 secondes.

Les dossiers `05_EXTRAITS_VIDEO`, `06_MONTAGES`, `07_SOUS_TITRES` et `08_EXPORTS_FINAUX` reçoivent les extraits, le montage paysage, les sous-titres et les exports 4:5. Le rapport se trouve dans `09_RAPPORTS`. Le dépôt versionne uniquement le code et sa documentation.
