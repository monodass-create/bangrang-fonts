"""방랑 UI / 방랑 기록체 0.1 — 외부 글꼴 윤곽을 읽지 않는 자체 글자 생성 원본.

한글 자모와 영문·숫자의 기본 선을 이 파일에서 직접 정의한다.
원형·선·끝 장식으로 윤곽을 만들고, 초성/중성/종성 배치에 따라 완성형을 구성한다.
필요 도구: Python 3, fontTools. 이미지 견본 생성에는 Pillow를 사용한다.
"""
from pathlib import Path
import math
import json
import hashlib
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
LEADS = list('ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ')
VOWELS = list('ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ')
TAILS = [''] + list('ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ')
PAIRS = {'ㄲ':'ㄱㄱ','ㄸ':'ㄷㄷ','ㅃ':'ㅂㅂ','ㅆ':'ㅅㅅ','ㅉ':'ㅈㅈ',
         'ㄳ':'ㄱㅅ','ㄵ':'ㄴㅈ','ㄶ':'ㄴㅎ','ㄺ':'ㄹㄱ','ㄻ':'ㄹㅁ',
         'ㄼ':'ㄹㅂ','ㄽ':'ㄹㅅ','ㄾ':'ㄹㅌ','ㄿ':'ㄹㅍ','ㅀ':'ㄹㅎ','ㅄ':'ㅂㅅ'}
MIXED = {'ㅘ':('ㅗ','ㅏ'),'ㅙ':('ㅗ','ㅐ'),'ㅚ':('ㅗ','ㅣ'),
         'ㅝ':('ㅜ','ㅓ'),'ㅞ':('ㅜ','ㅔ'),'ㅟ':('ㅜ','ㅣ'),'ㅢ':('ㅡ','ㅣ')}

class Ink:
    def __init__(self, display=False):
        self.pen=TTGlyphPen(None);self.display=display;self.weight=62 if display else 58
    def polygon(self, points, hole=False):
        # 화면식 y좌표를 폰트의 기준선 좌표로 변환한다. 구멍은 반대 방향 윤곽이다.
        p=[(round(x),round(800-y)) for x,y in points]
        area=sum(p[i][0]*p[(i+1)%len(p)][1]-p[(i+1)%len(p)][0]*p[i][1] for i in range(len(p)))
        if (area<0)!=hole:p.reverse()
        self.pen.moveTo(p[0])
        for q in p[1:]:self.pen.lineTo(q)
        self.pen.closePath()
    def disk(self,x,y,r):
        count=4 if self.display else 12
        self.polygon([(x+r*math.cos(t*math.tau/count),y+r*math.sin(t*math.tau/count)) for t in range(count)])
    def line(self,points,width=None):
        width=width or self.weight;r=width/2
        for (x,y),(a,b) in zip(points,points[1:]):
            d=math.hypot(a-x,b-y)
            if not d:continue
            nx,ny=-(b-y)/d*r,(a-x)/d*r
            self.polygon([(x+nx,y+ny),(a+nx,b+ny),(a-nx,b-ny),(x-nx,y-ny)])
        for x,y in points:self.disk(x,y,r if not self.display else r*.85)
        if self.display and len(points)>1:
            # 기록체만 끝을 벌린 쐐기 장식을 붙인다. UI체에는 장식이 없다.
            for (x,y),(a,b) in [(points[0],points[1]),(points[-1],points[-2])]:
                d=math.hypot(a-x,b-y)
                if d:
                    ux,uy=(a-x)/d,(b-y)/d;nx,ny=-uy,ux
                    self.polygon([(x+nx*r*1.65,y+ny*r*1.65),(x-nx*r*1.65,y-ny*r*1.65),(x+ux*r*1.8,y+uy*r*1.8)])
    def oval(self,x,y,rx,ry,width=None):
        r=(width or self.weight)/2
        count,phase=(8,math.pi/8) if self.display else (32,0)
        for hole,dx in [(False,r),(True,-r)]:
            self.polygon([(x+(rx+dx)*math.cos(phase+t*math.tau/count),y+(ry+dx)*math.sin(phase+t*math.tau/count)) for t in range(count)],hole)
    def glyph(self):
        g=self.pen.glyph()
        if g.numberOfContours>0:g.flags[0]|=0x40 # 겹치는 선 윤곽임을 래스터라이저에 알린다.
        return g

def jamo(ink,char,box):
    x,y,w,h=box
    def line(*p):ink.line([(x+a*w,y+b*h) for a,b in p])
    def oval(a,b,rx,ry):ink.oval(x+a*w,y+b*h,rx*w,ry*h)
    if char in PAIRS:
        a,b=PAIRS[char];jamo(ink,a,(x,y,w*.45,h));jamo(ink,b,(x+w*.55,y,w*.45,h));return
    if char=='ㄱ':line((.12,.15),(.87,.15),(.87,.85))
    elif char=='ㄴ':line((.13,.15),(.13,.85),(.87,.85))
    elif char=='ㄷ':line((.87,.15),(.13,.15),(.13,.85),(.87,.85))
    elif char=='ㄹ':line((.13,.15),(.87,.15),(.87,.5),(.13,.5),(.13,.85),(.87,.85))
    elif char=='ㅁ':line((.13,.15),(.87,.15),(.87,.85),(.13,.85),(.13,.15))
    elif char=='ㅂ':
        line((.13,.15),(.13,.85),(.87,.85),(.87,.15));line((.13,.48),(.87,.48))
    elif char=='ㅅ':line((.12,.85),(.5,.15),(.88,.85))
    elif char=='ㅇ':oval(.5,.5,.36,.35)
    elif char in ('ㅈ','ㅊ'):
        top=.32 if char=='ㅊ' else .15
        if char=='ㅊ':line((.35,.08),(.65,.08))
        line((.12,top),(.88,top));line((.12,.88),(.5,top+.06),(.88,.88))
    elif char=='ㅋ':line((.13,.15),(.87,.15),(.87,.85));line((.13,.5),(.87,.5))
    elif char=='ㅌ':line((.87,.15),(.13,.15),(.13,.85),(.87,.85));line((.13,.5),(.87,.5))
    elif char=='ㅍ':
        line((.1,.15),(.9,.15));line((.1,.85),(.9,.85));line((.3,.15),(.3,.85));line((.7,.15),(.7,.85))
    elif char=='ㅎ':line((.35,.08),(.65,.08));line((.1,.28),(.9,.28));oval(.5,.65,.31,.23)
    elif char in ('ㅏ','ㅐ','ㅑ','ㅒ','ㅓ','ㅔ','ㅕ','ㅖ','ㅣ'):
        if char=='ㅣ':line((.5,.08),(.5,.92));return
        right=char in 'ㅏㅐㅑㅒ';extra=char in 'ㅐㅒㅔㅖ';double=char in 'ㅑㅒㅕㅖ'
        stem=(.24 if right else .49) if extra else (.3 if right else .7)
        line((stem,.08),(stem,.92))
        for yy in ([.35,.65] if double else [.5]):
            line((stem,yy),((.56 if extra else .9) if right else .08,yy))
        if extra:line((.88,.08),(.88,.92))
    elif char in ('ㅗ','ㅛ','ㅜ','ㅠ','ㅡ'):
        if char=='ㅡ':line((.08,.5),(.92,.5));return
        up=char in 'ㅗㅛ';yy=.74 if up else .26
        line((.08,yy),(.92,yy))
        for xx in ([.34,.66] if char in 'ㅛㅠ' else [.5]):line((xx,yy),(xx,.08 if up else .92))
    elif char in MIXED:
        a,b=MIXED[char];jamo(ink,a,(x,y+h*.48,w*.63,h*.48));jamo(ink,b,(x+w*.68,y,w*.32,h))

def syllable(ink,cp):
    n=cp-0xac00;l=LEADS[n//588];v=VOWELS[n//28%21];t=TAILS[n%28]
    # 받침이 있을 때 윗부분을 줄이되, 글자 전체의 폭과 기준선은 고정한다.
    top=75;area=520 if t else 830
    if v in MIXED:
        a,b=MIXED[v]
        jamo(ink,l,(90,top,470,area*.59))
        jamo(ink,a,(65,top+area*.66,530,area*.32))
        jamo(ink,b,(650,top,275,area))
    elif v in 'ㅗㅛㅜㅠㅡ':
        jamo(ink,l,(145,top,710,area*.57));jamo(ink,v,(75,top+area*.68,850,area*.3))
    else:
        jamo(ink,l,(70,top+area*.06,475,area*.9));jamo(ink,v,(610,top,320,area))
    if t:jamo(ink,t,(115,650,770,300))

# 영문 대문자는 기존 글꼴에서 추출하지 않고 선의 좌표를 직접 설계한다.
CAPS={
'A':[[(70,800),(300,110),(530,800)],[(145,580),(455,580)]],
'B':[[(90,800),(90,110),(355,110),(510,210),(510,345),(355,450),(90,450)],[(355,450),(530,550),(530,690),(355,800),(90,800)]],
'C':[[(520,210),(410,110),(220,110),(85,250),(85,655),(220,800),(410,800),(520,700)]],
'D':[[(90,800),(90,110),(330,110),(520,285),(520,625),(330,800),(90,800)]],
'E':[[(520,110),(90,110),(90,800),(520,800)],[(90,450),(430,450)]],
'F':[[(90,800),(90,110),(520,110)],[(90,450),(430,450)]],
'G':[[(520,230),(410,110),(220,110),(85,250),(85,650),(220,800),(510,800),(510,480),(330,480)]],
'H':[[(90,110),(90,800)],[(520,110),(520,800)],[(90,455),(520,455)]],
'I':[[(150,110),(450,110)],[(300,110),(300,800)],[(150,800),(450,800)]],
'J':[[(170,110),(500,110),(500,650),(390,800),(210,800),(90,690)]],
'K':[[(90,110),(90,800)],[(520,110),(90,520),(520,800)]],
'L':[[(90,110),(90,800),(520,800)]],
'M':[[(70,800),(70,110),(300,485),(530,110),(530,800)]],
'N':[[(90,800),(90,110),(520,800),(520,110)]],
'O':[],
'P':[[(90,800),(90,110),(370,110),(520,230),(520,380),(370,500),(90,500)]],
'Q':[[(360,650),(560,870)]],
'R':[[(90,800),(90,110),(370,110),(520,230),(520,380),(370,500),(90,500)],[(330,500),(540,800)]],
'S':[[(520,200),(405,110),(215,110),(90,225),(90,355),(220,455),(400,455),(520,560),(520,680),(400,800),(210,800),(90,700)]],
'T':[[(60,110),(540,110)],[(300,110),(300,800)]],
'U':[[(90,110),(90,650),(210,800),(400,800),(520,650),(520,110)]],
'V':[[(70,110),(300,800),(530,110)]],
'W':[[(45,110),(150,800),(300,420),(450,800),(555,110)]],
'X':[[(70,110),(530,800)],[(530,110),(70,800)]],
'Y':[[(70,110),(300,450),(530,110)],[(300,450),(300,800)]],
'Z':[[(70,110),(530,110),(70,800),(530,800)]],
}

def latin(ink,c):
    if c in CAPS:
        if c in 'OQ':ink.oval(300,455,220,345)
        for p in CAPS[c]:ink.line(p)
        return 620
    if c.isdigit():
        paths={
        '1':[[(180,255),(320,110),(320,800)],[(160,800),(490,800)]],
        '2':[[(85,245),(190,110),(400,110),(520,240),(520,370),(85,800),(530,800)]],
        '3':[[(90,110),(510,110),(310,425),(470,455),(535,590),(500,720),(380,800),(200,800),(85,715)]],
        '4':[[(420,800),(420,110),(70,605),(550,605)]],
        '5':[[(520,110),(105,110),(105,425),(375,425),(520,545),(520,680),(400,800),(210,800),(85,720)]],
        '6':[[(490,140),(350,110),(200,225),(90,450),(90,650),(205,800),(410,800),(520,665),(520,530),(405,425),(200,425),(90,520)]],
        '7':[[(70,110),(530,110),(220,800)]],
        '9':[[(110,760),(250,800),(400,675),(520,450),(520,255),(405,110),(200,110),(90,245),(90,380),(205,485),(410,485),(520,390)]]}
        if c=='0':ink.oval(300,455,215,345);ink.line([(205,580),(395,330)],ink.weight*.8)
        elif c=='8':ink.oval(300,275,190,165);ink.oval(300,615,215,185)
        else:
            for p in paths[c]:ink.line(p)
        return 620
    # 소문자는 대문자 축소가 아니라 별도 높이·내림획을 갖도록 설계한다.
    if c in 'abdgopq':
        ink.oval(300,560,205,240)
        if c in 'ad':ink.line([(505,110 if c=='d' else 320),(505,800)])
        if c=='b':ink.line([(95,110),(95,800)])
        if c=='p':ink.line([(95,320),(95,990)])
        if c=='q':ink.line([(505,320),(505,990)])
        if c=='g':ink.line([(505,320),(505,870),(400,980),(220,980),(130,930)])
        return 620
    low={
    'c':[[(510,390),(410,320),(210,320),(90,445),(90,670),(210,800),(410,800),(510,730)]],
    'e':[[(95,555),(510,555),(510,440),(405,320),(210,320),(90,445),(90,665),(210,800),(410,800),(510,730)]],
    'f':[[(185,800),(185,230),(285,110),(435,110)],[(75,350),(390,350)]],
    'h':[[(95,110),(95,800)],[(95,445),(225,320),(380,320),(505,445),(505,800)]],
    'i':[[(205,335),(300,335),(300,800)],[(175,800),(425,800)]],
    'j':[[(240,335),(360,335),(360,875),(265,990),(140,990)]],
    'k':[[(95,110),(95,800)],[(500,320),(95,630),(515,800)]],
    'l':[[(180,110),(300,110),(300,720),(385,800),(450,800)]],
    'm':[[(65,800),(65,320)],[(65,415),(165,320),(240,320),(300,410),(300,800)],[(300,410),(400,320),(475,320),(550,410),(550,800)]],
    'n':[[(95,800),(95,320)],[(95,440),(220,320),(380,320),(505,440),(505,800)]],
    'r':[[(135,800),(135,320)],[(135,440),(265,320),(445,320)]],
    's':[[(500,380),(400,320),(205,320),(100,415),(100,490),(205,560),(390,560),(505,650),(505,710),(400,800),(205,800),(95,740)]],
    't':[[(240,155),(240,685),(330,800),(460,800)],[(90,340),(455,340)]],
    'u':[[(95,320),(95,680),(215,800),(375,800),(505,680)],[(505,320),(505,800)]],
    'v':[[(80,320),(300,800),(520,320)]],
    'w':[[(45,320),(155,800),(300,480),(445,800),(555,320)]],
    'x':[[(85,320),(515,800)],[(515,320),(85,800)]],
    'y':[[(80,320),(300,800)],[(520,320),(260,940),(160,990),(80,990)]],
    'z':[[(90,320),(510,320),(90,800),(510,800)]]}
    if c in low:
        for p in low[c]:ink.line(p)
        if c in 'ij':ink.disk(300 if c=='i' else 360,180,ink.weight*.72)
        return 620
    return punctuation(ink,c)

def punctuation(ink,c):
    if c in ' \u00a0':return 330
    if c=='\u3000':return 1000
    if c in '.,:;·':
        ys=[440,760] if c in ':;' else [470] if c=='·' else [760]
        for y in ys:ink.disk(170,y,ink.weight*.65)
        if c in ',;':ink.line([(180,775),(110,925)],ink.weight*.8)
        return 340
    if c in '!?':
        if c=='!':ink.line([(200,120),(200,570)])
        else:ink.line([(70,240),(150,120),(320,120),(405,240),(405,350),(225,480),(225,570)])
        ink.disk(200 if c=='!' else 225,760,ink.weight*.65);return 450
    if c in "'\"‘’“”`":
        ink.line([(150,100),(115,280)])
        if c in '\"“”':ink.line([(320,100),(285,280)])
        return 430 if c in '\"“”' else 260
    if c in '-–—_=':
        ys=[440,610] if c=='=' else [840] if c=='_' else [520]
        for y in ys:ink.line([(80,y),(520,y)])
        return 620
    if c in '/\\':ink.line([(100,800 if c=='/' else 110),(520,110 if c=='/' else 800)]);return 620
    if c in '()[]{}':
        p=[(330,70),(160,235),(110,455),(160,675),(330,840)] if c in '()' else [(340,70),(130,70),(130,840),(340,840)]
        if c in '{}':p=[(340,70),(210,160),(210,350),(100,455),(210,560),(210,750),(340,840)]
        if c in ')]}':p=[(440-x,y) for x,y in p]
        ink.line(p);return 450
    if c in '+<>|':
        if c=='+':ink.line([(80,470),(520,470)]);ink.line([(300,250),(300,690)])
        elif c=='|':ink.line([(180,100),(180,850)]);return 360
        else:ink.line([(470,200),(130,470),(470,740)] if c=='<' else [(130,200),(470,470),(130,740)])
        return 620
    if c=='…':
        for x in (130,310,490):ink.disk(x,760,ink.weight*.65)
        return 620
    if c in '←↑→↓':
        if c in '←→':
            ink.line([(80,470),(550,470)]);ink.line([(250,270),(80,470),(250,670)] if c=='←' else [(380,270),(550,470),(380,670)])
        else:
            ink.line([(310,170),(310,790)]);ink.line([(120,370),(310,170),(500,370)] if c=='↑' else [(120,590),(310,790),(500,590)])
        return 650
    if c=='#':
        for x in (225,425):ink.line([(x+50,120),(x-50,800)])
        for y in (350,590):ink.line([(80,y),(550,y)])
    elif c=='%':
        ink.oval(155,250,90,120);ink.oval(465,670,90,120);ink.line([(80,830),(540,90)])
    elif c=='*':
        for a in (0,math.pi/3,math.pi*2/3):ink.line([(310+220*math.cos(a),450+220*math.sin(a)),(310-220*math.cos(a),450-220*math.sin(a))])
    elif c=='^':ink.line([(90,350),(300,130),(510,350)])
    elif c=='~':ink.line([(80,500),(200,400),(410,540),(530,440)])
    elif c=='$':
        for p in CAPS['S']:ink.line(p)
        ink.line([(300,40),(300,880)],ink.weight*.7)
    elif c=='₩':
        for p in CAPS['W']:ink.line(p)
        for y in (360,500):ink.line([(40,y),(560,y)],ink.weight*.7)
    elif c=='&':ink.line([(520,800),(170,420),(100,260),(180,110),(320,110),(430,240),(360,370),(90,600),(100,740),(240,800),(400,740),(520,500)])
    elif c=='@':
        ink.oval(310,470,255,340);ink.oval(310,470,105,155);ink.line([(415,320),(415,620),(520,620)])
    else:
        # 미지원 문자의 대체 표시는 다른 지원 글자로 위장하지 않는 마름모다.
        ink.line([(310,120),(540,470),(310,820),(80,470),(310,120)])
    return 620

def build(display):
    family='Bangrang Chronicle' if display else 'Bangrang UI'
    korean='방랑 기록체' if display else '방랑 UI체'
    codes=set(range(32,127))|set(range(0xac00,0xd7a4))|set(map(ord,LEADS+VOWELS+TAILS[1:]))
    codes |= set(map(ord,'·–—‘’“”…₩←↑→↓\u00a0\u3000\ufffd'))
    codes |= set(range(0x1100,0x1113))|set(range(0x1161,0x1176))|set(range(0x11a8,0x11c3))
    glyphs={};metrics={};cmap={};order=['.notdef']
    ink=Ink(display);punctuation(ink,'\ufffd');glyphs['.notdef']=ink.glyph();metrics['.notdef']=(620,25)
    for cp in sorted(codes):
        ink=Ink(display);ch=chr(cp);advance=1000
        if 0xac00<=cp<=0xd7a3:syllable(ink,cp)
        elif ch in LEADS+VOWELS+TAILS[1:]:jamo(ink,ch,(90,100,820,780))
        elif 0x1100<=cp<=0x1112:jamo(ink,LEADS[cp-0x1100],(90,100,820,780))
        elif 0x1161<=cp<=0x1175:jamo(ink,VOWELS[cp-0x1161],(90,100,820,780))
        elif 0x11a8<=cp<=0x11c2:jamo(ink,TAILS[cp-0x11a7],(90,100,820,780))
        else:advance=latin(ink,ch)
        name=f'uni{cp:04X}';g=ink.glyph();glyphs[name]=g
        # hmtx 왼쪽 여백은 실제 윤곽의 최소 x와 일치시켜 줄 시작 위치를 보존한다.
        if g.numberOfContours:g.recalcBounds(glyphs);left=g.xMin
        else:left=0
        metrics[name]=(advance,left);cmap[cp]=name;order.append(name)
    fb=FontBuilder(1000,isTTF=True);fb.setupGlyphOrder(order);fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs);fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=900,descent=-250,lineGap=50)
    fb.setupNameTable({'familyName':family,'styleName':'Regular','uniqueFontIdentifier':family+' 0.1.0',
        'fullName':family+' Regular','psName':family.replace(' ','')+'-Regular','version':'Version 0.100',
        'copyright':'Copyright 2026 The Bangrang Font Project Authors.',
        'licenseDescription':'Licensed under the SIL Open Font License, Version 1.1. No Reserved Font Names.',
        'licenseInfoURL':'https://openfontlicense.org'})
    fb.setupOS2(version=4,sTypoAscender=900,sTypoDescender=-250,sTypoLineGap=50,usWinAscent=900,usWinDescent=250,
                usWeightClass=400,fsType=0,fsSelection=0xc0,sxHeight=480,sCapHeight=690)
    fb.setupPost();fb.setupMaxp()
    fb.font['name'].setName(korean,1,3,1,0x412);fb.font['name'].setName(korean+' Regular',4,3,1,0x412)
    out=ROOT/'fonts';out.mkdir(parents=True,exist_ok=True);path=out/(family.replace(' ','')+'-Regular.ttf');fb.save(path)
    font=TTFont(path);cmap2=font.getBestCmap()
    assert all(cp in cmap2 for cp in range(0xac00,0xd7a4))
    assert all(cp in cmap2 for cp in range(32,127))
    bounds=[]
    for name in font.getGlyphOrder():
        g=font['glyf'][name]
        if g.numberOfContours and (g.xMin < -10 or g.xMax > metrics[name][0]+10 or g.yMax > 1000 or g.yMin < -300):bounds.append(name)
    assert not bounds, bounds[:10]
    return {'family':family,'korean_name':korean,'file':path.name,'glyph_count':len(order),
            'hangul_syllables':11172,'ascii_printable':95,'unicode_codepoints':len(cmap2),
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'status':'0.1 prototype; full human readability review pending','bounds_check':'passed'}

if __name__=='__main__':
    results=[build(False),build(True)]
    (ROOT/'build-report.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(results,ensure_ascii=True,indent=2))
