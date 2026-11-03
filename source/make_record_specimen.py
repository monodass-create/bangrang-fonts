"""장문 흐름·표·인용·크기 비교를 실제 TTF로 조판하고 내용 보존을 검사한다."""
from pathlib import Path
import json,re,hashlib,html,argparse
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor,white
from fontTools.ttLib import TTFont as FontFile
from pypdf import PdfReader
import pdfplumber
from record_longform_content import TITLE,NOTICE,INTRO,SECTIONS,QUOTE,ROWS,CHECKS
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'specimens';OUT.mkdir(exist_ok=True)
FONTS=ROOT/'fonts';WORK=ROOT/'reviews';WORK.mkdir(exist_ok=True)
PDF=OUT/'참여자기록지-0.5.pdf';PAGE=(595.28,841.89)
for family,file in [('UI','BangrangUI-Regular.ttf'),('Chronicle','BangrangChronicle-Regular.ttf')]:
    pdfmetrics.registerFont(TTFont(family,str(FONTS/file)))
parser=argparse.ArgumentParser();parser.add_argument('--baseline',type=Path);args=parser.parse_args()
if args.baseline:pdfmetrics.registerFont(TTFont('OldUI',str(args.baseline)))
audit=[];expected=[]
INK=HexColor('#28332f');ACCENT=HexColor('#30574b');GRAY=HexColor('#63716a')
class CheckedParagraph(Paragraph):
    def draw(self):
        matrix=self.canv._currentMatrix;x,y=matrix[4],matrix[5]
        audit.append({'page':self.canv.getPageNumber(),'style':self.style.name,'x':x,'y':y,'width':self.width,'height':self.height,'text':self.getPlainText()})
        super().draw()
def style(name,size=11.5,leading=18,**kwargs):
    return ParagraphStyle(name,fontName='UI',fontSize=size,leading=leading,textColor=INK,
        spaceAfter=9,allowWidows=0,allowOrphans=0,splitLongWords=0,**kwargs)
BODY=style('body');H1=style('section',17,24,keepWithNext=True,spaceBefore=14,textTransform=None)
H1.textColor=ACCENT
NOTE=style('note',9,14);NOTE.textColor=GRAY
CELL=style('cell',10.5,16);CELL.spaceAfter=0
HEADER=style('table-header',10.5,16);HEADER.textColor=white
def p(text,s=BODY,check=True):
    if check:expected.append(text)
    return CheckedParagraph(html.escape(text),s)
class NumberedCanvas(canvas.Canvas):
    def showPage(self):
        # 페이지 상태를 복원하는 후처리 대신 각 페이지 종료 시 머리말·쪽수를 그린다.
        self.saveState();self.resetTransforms();header(self,None)
        self.setFont('UI',8);self.setFillColor(GRAY)
        self.drawString(64,35,'검수용 가상 기록 · 실제 참여자 평가가 아닙니다')
        self.drawRightString(PAGE[0]-64,35,str(self.getPageNumber()))
        self.restoreState();super().showPage()
def header(c,doc):
    c.saveState();c.setStrokeColor(HexColor('#d8e1dc'));c.setLineWidth(.55);c.line(64,787,PAGE[0]-64,787)
    c.setFont('UI',8.5);c.setFillColor(GRAY);c.drawString(64,802,'방랑 글꼴 0.5 | 장문 기록지 검수')
    c.drawRightString(PAGE[0]-64,802,'A4 · 본문 11.5pt / 줄 간격 18pt');c.restoreState()
doc=SimpleDocTemplate(str(PDF),pagesize=PAGE,leftMargin=64,rightMargin=64,topMargin=68,bottomMargin=67,
    title='방랑 글꼴 0.5 참여자 기록지 장문 검수',author='The Bangrang Font Project Authors')
title=style('title',27,36);title.fontName='Chronicle'
story=[p(TITLE,title),p('가상의 참여자 「여울」에게 · 조판 검수본',NOTE),p(NOTICE,NOTE),Spacer(1,5),p(INTRO)]
for heading,paras in SECTIONS:
    story.append(p(heading,H1))
    for paragraph in paras:story.append(p(paragraph))
story.extend([PageBreak(),p('활동 목록과 인용을 함께 읽기',H1),p('이 페이지의 내용도 앞선 가상 시나리오에 속합니다. 긴 문단 뒤에서 표의 항목과 상태를 빠르게 구별할 수 있는지, 숫자와 문장부호가 본문에 비해 과하게 눈에 띄지 않는지 확인합니다.')])
data=[[p(cell,HEADER if i==0 else CELL) for cell in row] for i,row in enumerate(ROWS)]
table=Table(data,colWidths=[76,269.28,110],repeatRows=1,hAlign='LEFT')
table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),ACCENT),('ROWBACKGROUNDS',(0,1),(-1,-1),[white,HexColor('#f3f6f4')]),
    ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
    ('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),('LINEBELOW',(0,-1),(-1,-1),.6,HexColor('#cbd8d0'))]))
story.extend([table,Spacer(1,18),p('직접 인용과 보충 설명',H1)])
quote=style('quote',13,21,leftIndent=16,rightIndent=16);quote.textColor=ACCENT
story.extend([p(QUOTE,quote),p('가상의 발언을 따옴표로 묶은 예시입니다. 인용 뒤의 설명은 별도 문단으로 배치했습니다. 실제 기록지를 작성할 때는 확인한 발언과 편집자의 요약을 같은 문장으로 합치지 않는 형식을 사용할 수 있습니다.'),p('※ 검수 메모: 이 견본은 실물 인쇄물이 아닙니다. PDF 내장 글꼴과 화면 출력, 인쇄용 해상도의 렌더링을 확인합니다.',NOTE)])
story.extend([PageBreak(),p('본문 크기와 읽기 간격 비교',H1),p('아래 세 문단은 같은 문장입니다. 문서의 글자 크기와 줄 간격을 함께 바꾸어 읽기 흐름을 비교합니다. 기본 기록지 본문은 11.5pt / 18pt로 작성했습니다.',NOTE)])
sample='젖은 흙을 골라 담은 뒤, 읽지 않은 장부와 남은 물품을 확인했습니다. 창고에 놓인 물통 3개와 널빤지 12개는 따로 적었습니다. “아직 확인하지 못했습니다”라는 문장은 그대로 남겼습니다. Inventory 12 / Tools 3. 다음 사람이 이어서 읽어도 완료한 일과 예정한 일을 구별할 수 있도록 문장을 나누었습니다.'
for size,leading in [(10.5,17),(11.5,18),(12,20)]:
    story.extend([p(f'{size}pt / {leading}pt',NOTE),p(sample,style(f'size-{size}',size,leading)),Spacer(1,12)])
story.append(p('공백과 괄호, 0.4 / 0.5 비교' if args.baseline else '공백과 괄호 확인',H1))
compare='기록을 읽고 (남은 일을 확인한 뒤) 다음 사람에게 전달했습니다. 함께 정리한 목록에는 물통 3개와 널빤지 12개가 있습니다.'
if args.baseline:
    old=style('compare-old');old.fontName='OldUI'
    story.extend([p('0.4 / 공백 330 단위',NOTE),p(compare,old)])
story.extend([p('0.5 / 공백 380 단위, 둥근 괄호 보완',NOTE),p(compare)])
story.extend([PageBreak(),p('복잡한 글자와 부호 확인',H1)])
for label,text in CHECKS:story.extend([p(label,H1),p(text)])
story.extend([Spacer(1,12),p('견본을 읽은 뒤 확인할 부분',H1),p('여러 쪽을 연속해서 읽을 때 다음 줄의 시작을 놓치는지, 비슷한 받침이나 숫자를 반복해서 확인하게 되는지 살펴봐 주세요. 실제 배포 원고를 넣을 때는 이름·날짜·단위와 본문에 쓰인 모든 문자의 지원 여부를 먼저 확인해야 합니다. 본문을 맞추려고 글자 사이를 강제로 늘리지 않고, 문단 사이 여백으로 내용의 구분을 드러내는 설정을 사용했습니다.'),p('※ 한자·일본어·옛한글·다른 굵기는 이번 글꼴의 지원 범위에 포함하지 않습니다. 실제 참여자에게 보낸 기록지 원본은 확보하지 못했으며, 이 문서는 그 원본의 복원본이 아닙니다.',NOTE)])
cm=FontFile(FONTS/'BangrangUI-Regular.ttf').getBestCmap()
missing=sorted({ch for text in expected for ch in text if not ch.isspace() and ord(ch) not in cm});assert not missing,missing
doc.build(story,canvasmaker=NumberedCanvas)
def compact(text):return re.sub(r'\s+','',text)
with pdfplumber.open(PDF) as pdf:
    texts=[page.crop((0,59,PAGE[0],790)).extract_text() or '' for page in pdf.pages]
combined=compact('\n'.join(texts))
lost=[s for s in expected if compact(s) not in combined]
assert not lost,lost[:2]
r=PdfReader(str(PDF));emb=[]
for page in r.pages:
    names=[]
    for obj in page['/Resources']['/Font'].values():
        font=obj.get_object();descriptor=font.get('/FontDescriptor')
        if descriptor and '/FontFile2' in descriptor.get_object():names.append(str(font['/BaseFont']))
    assert names;emb.append(names)
# 본문과 제목의 실제 배치만 자동 범위 검사를 하고 표는 페이지 이미지로 확인한다.
bad=[a for a in audit if a['style'] not in ('cell','table-header') and (a['y']<60 or a['y']+a['height']>780 or a['x']<60 or a['x']+a['width']>540)]
assert not bad,bad[:1]
report={'pages':len(r.pages),'narrative_characters_including_spaces':len(INTRO)+sum(len(x) for _,ps in SECTIONS for x in ps),
 'expected_text_blocks':len(expected),'text_blocks_preserved':not lost,'missing_supported_text_characters':missing,
 'body_size_pt':11.5,'leading_pt':18,'body_width_pt':PAGE[0]-128-12,'body_bounds_failures':bad,
 'embedded_fonts_per_page':emb,'source_scope':'Explicitly fictional typography sample, not a participant report or a reconstruction of Parfum',
 'font_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in FONTS.glob('*.ttf')}}
(WORK/'0.5-longform-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(WORK/'0.5-paragraph-layout.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
(OUT/'검수용-가상원고.txt').write_text(NOTICE+'\n\n'+INTRO+'\n\n'+'\n\n'.join(h+'\n\n'+'\n\n'.join(ps) for h,ps in SECTIONS),encoding='utf-8')
print(json.dumps(report,ensure_ascii=True))
