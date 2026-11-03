"""방랑 0.5 생성기: UI 윤곽 개선, 획 합집합, 메트릭·이름·버전 정합성.

legacy_v03.py는 프로젝트가 직접 만든 원본이다. 외부 글꼴 윤곽은 입력으로 사용하지 않는다.
"""
from pathlib import Path
import json,hashlib
from fontTools.ttLib import TTFont,newTable
from fontTools.ttLib.removeOverlaps import removeOverlaps
import legacy_v03 as base
import ui_shapes as shapes
from text_punctuation import refine
ROOT=Path(__file__).resolve().parents[1]
LEGACY_DRAWING={name:getattr(base,name) for name in ('Ink','jamo','syllable','latin')}

def names(f,family,korean):
    # 한국어·영어 버전과 식별자를 함께 갱신해 이전 시험안과 섞이지 않게 한다.
    for ident in [1,3,4,5,6,16]:f['name'].removeNames(nameID=ident)
    for ident,value in [(1,family),(3,family+' 0.5.0'),(4,family+' Regular'),(5,'Version 0.500'),(6,family.replace(' ','')+'-Regular'),(16,family)]:
        f['name'].setName(value,ident,3,1,0x409)
    for ident,value in [(1,korean),(4,korean+' Regular'),(16,korean)]:f['name'].setName(value,ident,3,1,0x412)
    f['head'].fontRevision=.5

def build():
    base.Ink=shapes.ModernInk;base.jamo=shapes.jamo;base.syllable=shapes.syllable;base.latin=shapes.latin;base.ROOT=ROOT
    base.build(False)
    path=ROOT/'fonts/BangrangUI-Regular.ttf';f=TTFont(path)
    # 한글 칸만 조금 좁혀 문장의 지나친 벌어짐을 줄인다. 영문 비례폭·숫자 고정폭은 유지한다.
    cmap=f.getBestCmap()
    for cp,name in cmap.items():
        if (0xac00<=cp<=0xd7a3) or (0x1100<=cp<=0x11ff) or (0x3130<=cp<=0x318f):
            g=f['glyf'][name]
            if g.numberOfContours:
                g.coordinates.scale((.94,1.08 if 0xac00<=cp<=0xd7a3 else 1))
                if 0xac00<=cp<=0xd7a3:g.coordinates.translate((0,5))
                g.recalcBounds(f['glyf'])
            f['hmtx'][name]=(940,g.xMin if g.numberOfContours else 0)
    # 겹친 선을 실제 합집합 윤곽으로 만들어 렌더러의 겹침 처리 차이를 줄인다.
    refine(f)
    removeOverlaps(f,ignoreErrors=False)
    names(f,'Bangrang UI','방랑 UI체')
    gasp=newTable('gasp');gasp.version=1;gasp.gaspRange={65535:10};f['gasp']=gasp
    f.save(path)
    # 기록체도 보존된 제작 좌표에서 재생성한다. 이전 TTF 파일을 입력으로 요구하지 않는다.
    for name,value in LEGACY_DRAWING.items():setattr(base,name,value)
    base.build(True)
    chronicle=TTFont(ROOT/'fonts/BangrangChronicle-Regular.ttf');names(chronicle,'Bangrang Chronicle','방랑 기록체')
    refine(chronicle,display=True)
    chronicle.save(ROOT/'fonts/BangrangChronicle-Regular.ttf')
    report=[]
    for file in sorted((ROOT/'fonts').glob('*.ttf')):
        current=TTFont(file);report.append({'file':file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
            'glyph_count':len(current.getGlyphOrder()),'codepoints':len(current.getBestCmap()),'version':current['name'].getDebugName(5)})
    (ROOT/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(report),flush=True)

if __name__=='__main__':build()
