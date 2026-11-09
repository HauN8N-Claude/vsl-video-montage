"""Production locale du scénario A validé. Aucun original modifié."""
import os
from pathlib import Path
import json,subprocess,math,textwrap,re,difflib,sys
from concurrent.futures import ThreadPoolExecutor,as_completed
from PIL import Image,ImageDraw,ImageFont
ROOT = Path(os.environ["VSL_PROJECT_DIR"]).expanduser().resolve(strict=True)
FF = os.environ.get("VSL_FFMPEG", "ffmpeg")
PROBE = os.environ.get("VSL_FFPROBE", "ffprobe")
FP = PROBE
SOURCE=ROOT/'01_SOURCES/VSL SOLAIRE V2.mp4'
for name in ('05_EXTRAITS_VIDEO','06_MONTAGES','07_SOUS_TITRES','08_EXPORTS_FINAUX','02_TRAVAIL/PCM','02_TRAVAIL/PRODUCTION','02_TRAVAIL/CONTROLE_EXPORTS'):(ROOT/name).mkdir(exist_ok=True,parents=True)
WORK=ROOT/'02_TRAVAIL/PRODUCTION'
def run(args,name):
    with (WORK/(name+'.log')).open('w',encoding='utf-8') as log:
        subprocess.run([FF,'-hide_banner','-nostdin',*args],stdout=log,stderr=subprocess.STDOUT,check=True)
def probe(p):return json.loads(subprocess.check_output([PROBE,'-v','error','-show_streams','-show_format','-of','json',str(p)]))
def write_once(path,text):
    if path.exists():return
    path.write_text(text,encoding='utf-8')
def font(n,bold=False):return ImageFont.truetype('C:/Windows/Fonts/arial'+('bd' if bold else '')+'.ttf',n)
def centered(draw,text,y,f,fill,width):
    for line in text.split('\n'):
        box=draw.textbbox((0,0),line,font=f);draw.text(((width-(box[2]-box[0]))/2,y),line,font=f,fill=fill);y+=int(f.size*1.3)
    return y
def background(size):
    im=Image.new('RGB',size,'#06080D');d=ImageDraw.Draw(im);w,h=size
    for j in range(18):
        points=[(int(w*k/80),int(h*.85+math.sin(k/17+j*.04)*h*.09+j*4)) for k in range(81)]
        d.line(points,fill=(17,49+j*2,80+j*3),width=1)
    return im
def cards():
    land=background((1920,1080));d=ImageDraw.Draw(land)
    d.text((95,60),os.environ.get("VSL_BRAND", "Studio VSL"),font=font(48,True),fill='#29B6F6')
    centered(d,'UN INSTALLATEUR PAR ZONE',240,font(78,True),'#F5F7FA',1920)
    centered(d,'Sous réserve de disponibilité',365,font(40),'#B6C2D2',1920)
    d.rounded_rectangle((160,520,1760,785),radius=25,fill='#0D1421',outline='#29B6F6',width=3)
    centered(d,'Première étape : formulaire\ndans la publication',560,font(58,True),'#F5F7FA',1920)
    centered(d,'Partenariat installateur photovoltaïque',895,font(34),'#B6C2D2',1920)
    land.save(WORK/'carton-paysage.png')
    canvas=background((1080,1350));d=ImageDraw.Draw(canvas)
    d.text((65,55),os.environ.get("VSL_BRAND", "Studio VSL"),font=font(40,True),fill='#29B6F6')
    centered(d,'LE MÉCANISME\nDE L’OFFRE',135,font(62,True),'#F5F7FA',1080)
    centered(d,'Formulaire dans la publication',1255,font(31),'#B6C2D2',1080)
    canvas.save(WORK/'toile-facebook.png')
    end=background((1080,1350));d=ImageDraw.Draw(end)
    d.text((65,55),os.environ.get("VSL_BRAND", "Studio VSL"),font=font(40,True),fill='#29B6F6')
    centered(d,'UN INSTALLATEUR\nPAR ZONE',290,font(65,True),'#F5F7FA',1080)
    centered(d,'Sous réserve de disponibilité',500,font(34),'#B6C2D2',1080)
    d.rounded_rectangle((60,665,1020,980),radius=24,fill='#0D1421',outline='#29B6F6',width=3)
    centered(d,'Première étape :\nformulaire dans\nla publication',705,font(51,True),'#F5F7FA',1080)
    end.save(WORK/'carton-facebook.png')

original=json.loads((ROOT/'04_ANALYSE_ET_TIMECODES/PLANS_MACHINE.json').read_text(encoding='utf-8'))['A']
names=['CIBLE','PROBLEME','DIFFERENCIATION','ACQUISITION','PRISE_EN_CHARGE','QUALIFICATION','RENDEZ_VOUS','ROLE_INSTALLATEUR','SUIVI_RELANCES','APPEL_ACTION','PARTENARIAT_FORMULAIRE']
seq=[];cursor=0
for i,c in enumerate(original['sequence']):
    c=dict(c);first=math.floor(c['start']*30+1e-6) if c['src']=='A' else 0;last=math.ceil(c['end']*30-1e-6)
    n=last-first;c.update(index=i+1,first_frame=first,last_frame=last,frames=n,start=first/30,end=last/30,duration=n/30,timeline_start=cursor/30,timeline_end=(cursor+n)/30,name=f'SEQ_{i+1:02}_{names[i]}')
    cursor+=n;seq.append(c)
TOTAL=cursor/30
assert TOTAL<=90
write_once(WORK/'chronologie-realisee.json',json.dumps(dict(validation='Scénario A sélectionné dans le plan de montage.',duration=TOTAL,frames=cursor,sequence=seq),ensure_ascii=False,indent=2))

def extract(c):
    target=ROOT/'05_EXTRAITS_VIDEO'/(c['name']+'.mp4');pcm=ROOT/'02_TRAVAIL/PCM'/(c['name']+'.wav')
    if target.exists() and pcm.exists():
        p=probe(target);v=next(s for s in p['streams'] if s['codec_type']=='video')
        if int(v.get('nb_frames',0))==c['frames']:return
        raise RuntimeError('Fichier existant non conforme : '+str(target))
    if target.exists() or pcm.exists():raise FileExistsError('Extraction partielle à vérifier : '+str(target))
    seconds=c['duration'];samples=c['frames']*1600
    if c['src']=='A':
        inp=['-ss',f'{c["start"]:.9f}','-threads','2','-i',str(SOURCE)]
        filters=f'[0:v]fps=30,trim=end_frame={c["frames"]},setpts=PTS-STARTPTS,setsar=1[v];[0:a]aresample=48000,apad,atrim=end_sample={samples},asetpts=PTS-STARTPTS,afade=t=in:d=0.003,afade=t=out:st={max(0,seconds-.004):.9f}:d=0.004,asplit=2[a][pcm]'
    else:
        inp=['-loop','1','-framerate','30','-i',str(WORK/'carton-paysage.png'),'-f','lavfi','-i','anullsrc=r=48000:cl=stereo']
        filters=f'[0:v]trim=end_frame={c["frames"]},setpts=PTS-STARTPTS,setsar=1[v];[1:a]atrim=end_sample={samples},asetpts=PTS-STARTPTS,asplit=2[a][pcm]'
    run(['-n','-filter_complex_threads','1',*inp,'-filter_complex',filters,'-map','[v]','-map','[a]','-frames:v',str(c['frames']),'-t',f'{seconds:.9f}','-c:v','libx264','-preset','fast','-crf','18','-threads','2','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-movflags','+faststart',str(target),'-map','[pcm]','-c:a','pcm_s24le','-ar','48000','-ac','2','-t',f'{seconds:.9f}',str(pcm)],c['name'])
    print('Extrait prêt : '+c['name'],flush=True)

def assemble():
    video=WORK/'piste-video.mp4';audio=WORK/'voix-continue.wav';norm=WORK/'voix-diffusion.m4a'
    listing=WORK/'liste-video.txt';listing.write_text(''.join("file '"+str((ROOT/'05_EXTRAITS_VIDEO'/(c['name']+'.mp4')).resolve()).replace('\\','/')+"'\n" for c in seq),encoding='utf-8')
    pcm_list=WORK/'liste-audio.txt';pcm_list.write_text(''.join("file '"+str((ROOT/'02_TRAVAIL/PCM'/(c['name']+'.wav')).resolve()).replace('\\','/')+"'\n" for c in seq),encoding='utf-8')
    if not video.exists():run(['-n','-f','concat','-safe','0','-i',str(listing),'-map','0:v:0','-an','-c:v','copy',str(video)],'assemblage-video')
    if not audio.exists():run(['-n','-f','concat','-safe','0','-i',str(pcm_list),'-c:a','pcm_s24le',str(audio)],'assemblage-audio')
    if not norm.exists():run(['-n','-i',str(audio),'-af','loudnorm=I=-18:TP=-1.5:LRA=11:print_format=json','-ar','48000','-ac','2','-c:a','aac','-b:a','192k','-t',f'{TOTAL:.9f}',str(norm)],'normalisation')
    # The approved card appears during the diagnostic CTA and holds 4.5 s afterward.
    landscape=ROOT/'06_MONTAGES/VSL_MECANISME_V1.mp4';cta=next(c['timeline_start'] for c in seq if c['id']=='cta')
    if not landscape.exists():run(['-n','-filter_complex_threads','1','-threads','2','-i',str(video),'-loop','1','-framerate','30','-i',str(WORK/'carton-paysage.png'),'-i',str(norm),'-filter_complex',f'[0:v][1:v]overlay=0:0:enable=\'gte(t,{cta:.9f})\':shortest=1,format=yuv420p[v]','-map','[v]','-map','2:a:0','-frames:v',str(cursor),'-t',f'{TOTAL:.9f}','-c:v','libx264','-crf','18','-preset','fast','-threads','3','-c:a','copy','-movflags','+faststart',str(landscape)],'montage-paysage')
    return landscape,cta

def normalize(w):return re.sub(r'[^a-z0-9àâäéèêëîïôöùûüç]','',w.lower().replace('’',"'"))
def source_words(c):
    windows={'adresse':'A-intro','difference':'A-differenciation','ads':'A-campagnes','questions':'A-questions','rdv':'A-rendezvous','relances':'A-relances'}
    if c['id'] in windows:data=json.loads((ROOT/'02_TRAVAIL'/f'verification-{windows[c["id"]]}.json').read_text(encoding='utf-8'))
    else:data=json.loads((ROOT/'03_TRANSCRIPTIONS/VSL_SOLAIRE_BRUT.json').read_text(encoding='utf-8'))
    raw=[dict(w) for s in data['segments'] for w in s.get('words',[]) if w['start']>=c['start']-.04 and w['start']<c['end']-.02]
    merged=[]
    for w in raw:
        if not normalize(w['text']):
            if merged:merged[-1]['text']+=w['text']
            continue
        if merged and (w['text'].startswith(("'",'’','-')) or merged[-1]['text'].endswith(("'",'’'))):
            merged[-1]['text']+=w['text'];merged[-1]['end']=w['end']
        else:merged.append(w)
    return merged
def subtitle_words(c):
    source=source_words(c);target=c['text'].split()
    # Map editorial punctuation/spelling onto independently timestamped spoken tokens.
    matching=difflib.SequenceMatcher(a=[normalize(x) for x in target],b=[normalize(w['text']) for w in source],autojunk=False)
    positions={}
    for block in matching.get_matching_blocks():
        for i in range(block.size):positions[block.a+i]=source[block.b+i]
    result=[]
    for i,t in enumerate(target):
        if i in positions:w=positions[i];start=w['start'];end=w['end']
        else:
            before=max([j for j in positions if j<i],default=-1);after=min([j for j in positions if j>i],default=len(target))
            lo=positions[before]['end'] if before>=0 else c['start'];hi=positions[after]['start'] if after<len(target) else c['end']
            start=lo+(hi-lo)*(i-before-1)/(after-before);end=lo+(hi-lo)*(i-before)/(after-before)
        result.append(dict(text=t,start=max(c['timeline_start'],c['timeline_start']+start-c['start']),end=min(c['timeline_end'],c['timeline_start']+end-c['start'])))
    return result
def stamp(t,ass=False):
    if ass:
        n=round(t*100);return f'{n//360000}:{n//6000%60:02}:{n//100%60:02}.{n%100:02}'
    n=round(t*1000);return f'{n//3600000:02}:{n//60000%60:02}:{n//1000%60:02},{n%1000:03}'
def subtitles():
    cues=[];mapped=[]
    captions_file = Path(os.environ.get("VSL_CAPTIONS_FILE", Path(__file__).resolve().parent.parent / "local" / "phrases.json"))
    phrases = json.loads(captions_file.read_text(encoding="utf-8"))
    for c in seq:
        if c['src']!='A':continue
        words=subtitle_words(c);mapped+=words;chunks=[];offset=0
        assert [normalize(w) for phrase in phrases[c['id']] for w in phrase.split()]==[normalize(w['text']) for w in words],c['id']
        for phrase in phrases[c['id']]:
            n=len(phrase.split());chunks.append(words[offset:offset+n]);offset+=n
        for i,chunk in enumerate(chunks):
            start=max(c['timeline_start'],chunk[0]['start'])
            end=min(c['timeline_end'],(chunks[i+1][0]['start']-.01 if i+1<len(chunks) else c['timeline_end']-.01))
            assert end-start>.4,(c['id'],chunk,start,end)
            text=' '.join(w['text'] for w in chunk)
            if len(text)<=38:wrapped=[text]
            else:
                tokens=text.split();options=[]
                for split in range(1,len(tokens)):
                    a=' '.join(tokens[:split]);b=' '.join(tokens[split:])
                    if max(len(a),len(b))>38:continue
                    orphan=normalize(tokens[split-1]) in {'de','des','du','dun','un','une','et','à','en','pour','sur','le','la','les','votre','vos','ses','qui','que'}
                    options.append((abs(len(a)-len(b))+(20 if orphan else 0),[a,b]))
                assert options,text
                wrapped=min(options,key=lambda item:item[0])[1]
            assert len(wrapped)<=2,(text,wrapped)
            cues.append(dict(start=round(start,3),end=round(end,3),text='\n'.join(wrapped)))
    assert all(a['end']<=b['start'] for a,b in zip(cues,cues[1:]))
    srt='\n\n'.join(f'{i}\n{stamp(q["start"])} --> {stamp(q["end"])}\n{q["text"]}' for i,q in enumerate(cues,1))+'\n'
    write_once(ROOT/'07_SOUS_TITRES/VSL_MECANISME.srt',srt)
    header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1350
WrapStyle: 2
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H00FFFFFF,&H00FFFFFF,&H00101421,&H00101421,1,0,0,0,100,100,0,0,3,10,0,2,65,65,165,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    lines=[]
    for q in cues:
        text=q['text'].replace('\n',r'\N');lines.append(f'Dialogue: 0,{stamp(q["start"],True)},{stamp(q["end"],True)},Default,,0,0,0,,{text}')
    write_once(ROOT/'07_SOUS_TITRES/VSL_MECANISME.ass',header+'\n'.join(lines)+'\n')
    write_once(WORK/'sous-titres-reperes.json',json.dumps(dict(cues=cues,words=mapped),ensure_ascii=False,indent=2))
    return cues

def exports(landscape,cta):
    base=ROOT/'08_EXPORTS_FINAUX/VSL_MECANISME_SANS_ST.mp4'
    active="[1:v]scale=1080:608:flags=lanczos,setsar=1[scene];[0:v][scene]overlay=0:330:shortest=1[composite];[composite][2:v]overlay=0:0:enable='gte(t,"+f'{cta:.9f}'+")':shortest=1,format=yuv420p[v]"
    if not base.exists():run(['-n','-filter_complex_threads','1','-loop','1','-framerate','30','-i',str(WORK/'toile-facebook.png'),'-threads','2','-i',str(landscape),'-loop','1','-framerate','30','-i',str(WORK/'carton-facebook.png'),'-filter_complex',active,'-map','[v]','-map','1:a:0','-frames:v',str(cursor),'-t',f'{TOTAL:.9f}','-c:v','libx264','-crf','18','-preset','fast','-threads','3','-c:a','copy','-movflags','+faststart',str(base)],'export-sans-st')
    final=ROOT/'08_EXPORTS_FINAUX/VSL_MECANISME_FACEBOOK.mp4'
    # Run from the project directory to keep the ASS filter path simple on Windows.
    ass="ass=07_SOUS_TITRES/VSL_MECANISME.ass"
    if not final.exists():run(['-n','-threads','1','-i',str(base),'-filter_threads','1','-vf',ass,'-frames:v',str(cursor),'-c:v','libx264','-crf','18','-preset','ultrafast','-tune','zerolatency','-threads','1','-c:a','copy','-movflags','+faststart',str(final)],'export-facebook')
    sub=ROOT/'06_MONTAGES/VSL_MECANISME_SOUS_TITREE.mp4'
    if not sub.exists():
        import os;os.link(final,sub)
    return [landscape,base,final]

if __name__=='__main__':
    import os;os.chdir(ROOT)
    cards()
    with ThreadPoolExecutor(max_workers=2) as pool:
        for task in as_completed([pool.submit(extract,c) for c in seq]):task.result()
    landscape,cta=assemble();cues=subtitles();outputs=exports(landscape,cta)
    report=dict(duration=TOTAL,frames=cursor,cues=len(cues),files=[dict(path=str(p),metadata=probe(p)) for p in outputs])
    write_once(ROOT/'09_RAPPORTS/PRODUCTION_A.json',json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(dict(duration=TOTAL,frames=cursor,cues=len(cues),outputs=[str(p) for p in outputs]),ensure_ascii=False),flush=True)
