"""장문용 변경의 범위와 새 문장부호를 확인한다. 가독성 실험을 대신하지 않는다."""
from pathlib import Path
import json,hashlib,sys
from fontTools.ttLib import TTFont
from PIL import Image,ImageDraw,ImageFont,ImageChops
ROOT=Path(__file__).resolve().parents[1]
BASE=Path(sys.argv[1]) if len(sys.argv)>1 else None
assert BASE and BASE.is_dir(),'Pass the preserved v0.4 fonts directory'
results=[]
for filename in ('BangrangUI-Regular.ttf','BangrangChronicle-Regular.ttf'):
    old=TTFont(BASE/filename);new=TTFont(ROOT/'fonts'/filename)
    a,b=old.getBestCmap(),new.getBestCmap()
    unchanged=0
    for cp in range(0xac00,0xd7a4):
        assert old['glyf'][a[cp]].compile(old['glyf'])==new['glyf'][b[cp]].compile(new['glyf']),hex(cp)
        assert old['hmtx'][a[cp]]==new['hmtx'][b[cp]],hex(cp)
        unchanged+=1
    added=sorted(set(b)-set(a));assert added==sorted(map(ord,'「」『』〈〉《》※'))
    sizes=[]
    for size in (12,14,16,18,24,48):
        f=ImageFont.truetype(str(ROOT/'fonts'/filename),size)
        for c in '「」『』〈〉《》※()':assert f.getmask(c).getbbox(),(filename,size,c)
        sizes.append(size)
    # 열고 닫는 부호의 외곽은 서로 다르며, 낫표의 가로 선은 반대 높이에 있어야 한다.
    for opening,closing in [('「','」'),('『','』')]:
        glyphs=[]
        for c in (opening,closing):
            g=new['glyf'][b[ord(c)]];g.recalcBounds(new['glyf'])
            glyphs.append(g)
        assert glyphs[0].compile(new['glyf'])!=glyphs[1].compile(new['glyf'])
        # 실제 래스터 상단·하단 가로획의 잉크량을 비교한다.
        f=ImageFont.truetype(str(ROOT/'fonts'/filename),100)
        totals=[]
        for c in (opening,closing):
            mask=f.getmask(c);im=Image.new('L',mask.size);im.putdata(list(mask))
            sums=[sum(im.crop((0,0,im.width,im.height//4)).tobytes()),sum(im.crop((0,im.height*3//4,im.width,im.height)).tobytes())]
            totals.append(sums)
        assert totals[0][0]>totals[0][1] and totals[1][1]>totals[1][0],(filename,totals)
    if 'Chronicle' in filename:
        for cp,name in a.items():
            assert old['glyf'][name].compile(old['glyf'])==new['glyf'][b[cp]].compile(new['glyf'])
            assert old['hmtx'][name]==new['hmtx'][b[cp]]
    results.append({'font':filename,'sha256':hashlib.sha256((ROOT/'fonts'/filename).read_bytes()).hexdigest(),
        'hangul_outlines_and_advances_unchanged_from_04':unchanged,'added_codepoints':[hex(cp) for cp in added],
        'new_punctuation_raster_sizes':sizes,'corner_quote_open_close_orientation':'passed',
        'space_advance':new['hmtx'][b[32]][0]})
(ROOT/'longtext-font-validation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(results))
