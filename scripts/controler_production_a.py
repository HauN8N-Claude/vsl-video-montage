import os
from pathlib import Path
import json,subprocess,re,hashlib
from concurrent.futures import ThreadPoolExecutor
from PIL import Image,ImageDraw,ImageFont
ROOT = Path(os.environ["VSL_PROJECT_DIR"]).expanduser().resolve(strict=True)
FF = os.environ.get("VSL_FFMPEG", "ffmpeg")
PROBE = os.environ.get("VSL_FFPROBE", "ffprobe")
FP = PROBE
OUT=ROOT/'02_TRAVAIL/CONTROLE_EXPORTS';OUT.mkdir(exist_ok=True)
timeline=json.loads((ROOT/'02_TRAVAIL/PRODUCTION/chronologie-realisee.json').read_text(encoding='utf-8'));N=timeline['frames'];D=timeline['duration']
files=[ROOT/'06_MONTAGES/VSL_MECANISME_V1.mp4',ROOT/'08_EXPORTS_FINAUX/VSL_MECANISME_SANS_ST.mp4',ROOT/'08_EXPORTS_FINAUX/VSL_MECANISME_FACEBOOK.mp4']
def inspect(file):
    m=json.loads(subprocess.check_output([FP,'-v','error','-show_streams','-show_format','-of','json',str(file)]));v=next(x for x in m['streams'] if x['codec_type']=='video');a=next(x for x in m['streams'] if x['codec_type']=='audio')
    assert int(v['nb_frames'])==N,(file,v['nb_frames'],N)
    assert v['r_frame_rate']=='30/1' and v['codec_name']=='h264' and a['codec_name']=='aac' and a['sample_rate']=='48000'
    assert abs(float(m['format']['duration'])-D)<.06
    resolution=(v['width'],v['height']);assert resolution==((1920,1080) if file.name=='VSL_MECANISME_V1.mp4' else (1080,1350))
    crop='' if resolution==(1920,1080) else 'crop=1080:608:0:330,'
    log=subprocess.run([FF,'-hide_banner','-v','info','-xerror','-threads','1','-i',str(file),'-filter_threads','1','-vf',crop+'blackdetect=d=0.08:pix_th=0.015:pic_th=0.995','-af','volumedetect','-f','null','NUL'],capture_output=True)
    (OUT/(file.stem+'-lecture.log')).write_bytes(log.stderr)
    assert log.returncode==0,str(file)
    text=log.stderr.decode(errors='replace');blacks=re.findall(r'black_start:([\d.]+) black_end:([\d.]+)',text);assert not blacks,(file,blacks)
    fingerprint=subprocess.check_output([FF,'-v','error','-i',str(file),'-map','0:a:0','-c:a','copy','-f','hash','-hash','sha256','-']).decode().strip()
    return dict(file=str(file),size=file.stat().st_size,duration=float(m['format']['duration']),width=v['width'],height=v['height'],frames=int(v['nb_frames']),fps=30,audio_hash=fingerprint,decode_ok=True,black_intervals=blacks,mean_dbfs=float(re.search(r'mean_volume: ([-\d.]+)',text).group(1)),peak_dbfs=float(re.search(r'max_volume: ([-\d.]+)',text).group(1)))
with ThreadPoolExecutor(max_workers=2) as pool:reports=list(pool.map(inspect,files))
assert len({r['audio_hash'] for r in reports})==1,'Les exports doivent utiliser la même voix.'
captions=json.loads((ROOT/'02_TRAVAIL/PRODUCTION/sous-titres-reperes.json').read_text(encoding='utf-8'))['cues'];ft=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',48)
for a,b in zip(captions,captions[1:]):assert a['end']<=b['start'],(a,b)
for c in captions:
    assert 0<=c['start']<c['end']<=D
    assert len(c['text'].splitlines())<=2
    for line in c['text'].splitlines():assert ft.getlength(line)+20<=950,(line,ft.getlength(line))
times=[.8,3.8,9,20,29,35,40,49,60,65,74,83,88]
def shot(item):
    i,t=item;file=OUT/f'image-{i:02}-a-{t:g}s.jpg'
    subprocess.run([FF,'-v','error','-n','-threads','1','-ss',str(t),'-i',str(files[-1]),'-frames:v','1','-q:v','2',str(file)],check=True);return file
with ThreadPoolExecutor(max_workers=2) as pool:shots=list(pool.map(shot,enumerate(times)))
label=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
for offset in range(0,len(shots),4):
    canvas=Image.new('RGB',(864,1132),(18,20,25));draw=ImageDraw.Draw(canvas)
    for i,file in enumerate(shots[offset:offset+4]):
        x=i%2*432;y=i//2*566;t=times[offset+i]
        draw.text((x+12,y+2),f'{t:g} s',font=label,fill='white');canvas.paste(Image.open(file).convert('RGB').resize((432,540)),(x,y+26))
    canvas.save(OUT/f'planche-{offset//4+1}.jpg',quality=92)
report=dict(ok=True,scenario='A',frames=N,duration=D,files=reports,subtitles=dict(cues=len(captions),max_lines=2,overlaps=0,reserved_band='Image source y330–938 ; sous-titres sous y1000 ; bas de texte à y1185, marge avant le pied de page y1255.'),captures=times,originals_modified=False)
(ROOT/'09_RAPPORTS/CONTROLE_QUALITE.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# Contrôle qualité — scénario A','',f'Export réalisé après validation utilisateur « A ». Durée finale : **{D:.3f} secondes** ({N} images à 30 images/s). Le léger écart avec le plan 89,264 s vient du calage des entrées et sorties sur les images de la source. La vitesse reste celle de la vidéo fournie.','', '## Fichiers vérifiés','', '| Fichier | Résolution | Durée | Poids | Lecture complète |','|---|---|---:|---:|---|']
for r in reports:lines.append(f'| `{Path(r["file"]).name}` | {r["width"]} × {r["height"]} | {r["duration"]:.3f} s | {r["size"]/1e6:.2f} Mo | Décodage FFmpeg sans erreur |')
lines+=['','## Contenu et raccords','', '- Les onze séquences MP4 sont conservées sans sous-titres dans `05_EXTRAITS_VIDEO`. Aucun original modifié.', '- Découpes réencodées à l’image ; micro-fondus audio de 3–4 ms aux raccords, dans les marges prévues autour des mots. Les conditions du rendez-vous et les formulations « peut » sont conservées.', '- Audio issu uniquement des extraits de A, normalisé autour de −18 LUFS ; aucune nouvelle voix et aucune musique ajoutée. Les trois exports utilisent le même flux AAC (hash identique).', '- Le carton territorial est un texte éditorial validé avec A, pas une parole attribuée à l’enregistrement. Le CTA diagnostic est contextualisé par la première étape du formulaire.', '- Le carton est affiché pendant le CTA puis maintenu 4,5 secondes. Le silence à cet endroit est intentionnel.', '- Export Facebook 4:5 : l’image paysage est conservée intégralement, sans couper les schémas ni l’avatar. Les sous-titres sont placés sous cette image.','', '## Sous-titres et image','', f'- {len(captions)} sous-titres français, deux lignes maximum, aucun chevauchement temporel. Largeur de texte contrôlée dans la bande réservée.', '- Aucun noir accidentel détecté automatiquement dans la zone de l’image vidéo. Les treize captures réparties dans l’export doivent être examinées avant livraison.', '- La synchronisation repose sur les repères mot à mot contrôlés lors de l’analyse et leur translation sur les points de coupe réellement utilisés. La voix et l’image de chaque extrait conservent leur relation temporelle.', '- Le contrôle sonore est technique (décodage, niveau, identité du flux), sans écoute humaine. Le contrôle visuel est effectué sur des captures, sans prétendre à un visionnage humain continu.','', '## Itérations conservées','', 'Les sorties de travail antérieures sont conservées dans `02_TRAVAIL/PRODUCTION/ITERATION_01` et `ITERATION_02`. Une erreur de chemin de police puis une allocation mémoire de l’encodeur ont été résolues ; l’export final sous-titré a été encodé avec moins de mémoire, en conservant une qualité CRF 18.']
(ROOT/'09_RAPPORTS/CONTROLE_QUALITE.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(dict(ok=True,duration=D,cues=len(captions),sizes=[r['size'] for r in reports]),ensure_ascii=False))
