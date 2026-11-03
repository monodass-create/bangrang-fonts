"""실제 TTF와 렌더링 결과에서 0.1의 재발 결함을 검사한다. 한국어 설명 포함."""
from pathlib import Path
import hashlib, json, struct
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

ROOT=Path(__file__).resolve().parents[1]

def connected_ink(path, char):
    # 크게 렌더링한 픽셀에서 획의 접촉을 검사한다. 작은 글자 가독성 판정은 별도 견본 검수다.
    im=Image.new('L',(300,300))
    ImageDraw.Draw(im).text((30,30),char,font=ImageFont.truetype(str(path),200),fill=255)
    mask={(x,y) for y in range(300) for x in range(300) if im.getpixel((x,y))>=128}
    count=0
    while mask:
        count+=1;todo=[mask.pop()]
        while todo:
            x,y=todo.pop()
            for dx,dy in ((0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)):
                p=x+dx,y+dy
                if p in mask:mask.remove(p);todo.append(p)
    return count

results=[]
for path in sorted((ROOT/'fonts').glob('*.ttf')):
    f=TTFont(path,checkChecksums=2)
    for tag in f.reader.keys():f.reader[tag];f[tag]
    cmap=f.getBestCmap();glyf=f['glyf'];metrics=f['hmtx']
    def outline(ch):return hashlib.sha256(glyf[cmap[ord(ch)]].compile(glyf)).hexdigest()
    assert all(cp in cmap and glyf[cmap[cp]].numberOfContours>0 for cp in range(0xac00,0xd7a4))
    assert len({outline(chr(cp)) for cp in range(0xac00,0xd7a4)})==11172
    assert all(cp in cmap for cp in range(32,127))
    assert all(ord(ch) in cmap for ch in '×÷±°℃✓•é')
    assert metrics[cmap[ord('W')]][0]>metrics[cmap[ord('i')]][0]
    assert len({metrics[cmap[ord(ch)]][0] for ch in '0123456789'})==1
    for group in ("'‘’`",'"“”','-–—','Il1','O0'):
        assert len({outline(ch) for ch in group})==len(group),group
    assert metrics[cmap[ord('-')]][0]<metrics[cmap[ord('–')]][0]<metrics[cmap[ord('—')]][0]
    assert 'GPOS' in f
    assert abs(f['head'].fontRevision-.3)<.00001
    assert f['name'].getDebugName(5)=='Version 0.300'
    bounds=[]
    for name in f.getGlyphOrder():
        g=glyf[name]
        if not g.numberOfContours:continue
        assert g.yMax<=f['OS/2'].usWinAscent and g.yMin>=-f['OS/2'].usWinDescent,name
        assert g.xMin>=0 and g.xMax<=metrics[name][0],name
        bounds.append((g.xMin,g.yMin,g.xMax,g.yMax))
    data=path.read_bytes();pad=data+b'\0'*((-len(data))%4)
    assert sum(struct.unpack('>'+str(len(pad)//4)+'I',pad))&0xffffffff==0xb1b0afba
    components={ch:connected_ink(path,ch) for ch in '흙홋획않좋'}
    assert components=={'흙':6,'홋':5,'획':6,'않':6,'좋':5},components
    results.append({'font':path.name,'sha256':hashlib.sha256(data).hexdigest(),
        'status':'passed','checks':['all modern Hangul nonempty and distinct','ASCII and selected symbols',
        'proportional Latin and tabular digits','distinct punctuation','version consistency',
        'whole file and table checksums','outline bounds','rendered stroke separation'],
        'rendered_connected_components_200px':components,
        'limits':'Not all-glyph human readability, cross-platform installation or usability certification'})
(ROOT/'regression-validation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(results,ensure_ascii=True))
