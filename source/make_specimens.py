"""완성 TTF를 다시 읽고 실제 렌더링한 견본을 만든다. 외부 글꼴은 사용하지 않는다."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'specimens';OUT.mkdir(exist_ok=True)
files=[ROOT/'fonts/BangrangUI-Regular.ttf',ROOT/'fonts/BangrangChronicle-Regular.ttf']
report=[]
for path in files:
    font=TTFont(path,checkChecksums=2);cmap=font.getBestCmap();glyf=font['glyf']
    seen={};duplicate=[];bounds=[10000,10000,-10000,-10000]
    for cp in range(0xac00,0xd7a4):
        assert cp in cmap
        g=glyf[cmap[cp]];assert g.numberOfContours>0
        digest=hashlib.sha256(g.compile(glyf)).hexdigest()
        if digest in seen:duplicate.append([hex(cp),hex(seen[digest])])
        seen[digest]=cp
        bounds=[min(bounds[0],g.xMin),min(bounds[1],g.yMin),max(bounds[2],g.xMax),max(bounds[3],g.yMax)]
    assert not duplicate,duplicate[:10]
    for cp in range(33,127):assert glyf[cmap[cp]].numberOfContours>0
    samples=['방랑 가나다 값 꽃 삶 읽다 굶다 밖 왜 돼 뷁 힣','Agjy WIM il1 0123456789',
             '소지품 배낭 제작 창고 건강 퀘스트','ㄱㄲㄳㄴㄵㄶㄹㄺㄻㄼㄽㄾㄿㅀㅄ ㅏㅐㅑㅒㅓㅔㅕㅖㅘㅙㅚㅝㅞㅟㅢ']
    for size in (11,13,15,18,24,48):
        raster=ImageFont.truetype(str(path),size)
        for text in samples:assert raster.getmask(text).getbbox()
    report.append({'font':path.name,'hangul_present_nonempty_distinct':11172,
                   'ascii_printable_present':95,'duplicate_hangul_outlines':len(duplicate),
                   'hangul_bounds':bounds,'raster_sizes_checked':[11,13,15,18,24,48],
                   'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                   'human_review':'representative images only; not all syllables or all applications'})

im=Image.new('RGB',(1440,1120),(243,239,225));d=ImageDraw.Draw(im)
for i,p in enumerate(files):
    y=25+i*550;ink=(29,45,43) if i==0 else (63,40,26)
    d.text((40,y),'방랑 UI체  /  Bangrang UI' if i==0 else '방랑 기록체  /  Bangrang Chronicle',font=ImageFont.truetype(str(p),46),fill=ink)
    d.text((40,y+94),'개척자의 기록 · 북방의 오래된 길',font=ImageFont.truetype(str(p),48),fill=ink)
    d.text((40,y+189),'한글 가나다 값 꽃 삶 읽다 굶다 왜 돼 뷁 힣',font=ImageFont.truetype(str(p),36),fill=ink)
    d.text((40,y+267),'ABCDEFGHIJKLMNOPQRSTUVWXYZ',font=ImageFont.truetype(str(p),38),fill=ink)
    d.text((40,y+335),'abcdefghijklmnopqrstuvwxyz 0123456789',font=ImageFont.truetype(str(p),38),fill=ink)
    d.text((40,y+416),'소지품 / 배낭 / 제작 / 창고 [L]   Wood 12 / Stone 34',font=ImageFont.truetype(str(p),24),fill=ink)
im.save(OUT/'두서체-견본.png')

im=Image.new('RGB',(1440,1050),(23,30,29));d=ImageDraw.Draw(im)
for i,p in enumerate(files):
    y=18+i*515
    d.text((35,y),'Bangrang UI' if i==0 else 'Bangrang Chronicle',font=ImageFont.truetype(str(p),32),fill=(233,218,185))
    for j,size in enumerate((11,13,15,18,24,32)):
        d.text((35,y+75+j*65),f'{size}px  소지품 배낭 제작 창고 [L]  값 꽃 삶 읽다 굶다  Agjy 0123456789',font=ImageFont.truetype(str(p),size),fill=(224,230,217))
im.save(OUT/'작은글자-검수.png')

# 초성·중성 조합을 골고루 볼 수 있는 대표 표. 전체 글자 육안 검수로 간주하지 않는다.
for i,p in enumerate(files):
    im=Image.new('RGB',(1240,1440),(248,247,242));d=ImageDraw.Draw(im);f=ImageFont.truetype(str(p),34)
    for lead in range(19):
        for vowel in range(21):
            cp=0xac00+lead*588+vowel*28+(0 if lead%3==0 else 8 if lead%3==1 else 27)
            d.text((30+vowel*57,20+lead*73),chr(cp),font=f,fill=(26,35,34))
    im.save(OUT/('UI체-조합검수.png' if i==0 else '기록체-조합검수.png'))
(ROOT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=True,indent=2))
