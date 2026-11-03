"""직접 설계한 현대 UI체의 곡선과 자모. 외부 글꼴 윤곽을 읽지 않는다."""
import math
import legacy_v03 as base
OriginalInk=base.Ink;original_jamo=base.jamo;original_latin=base.latin

class ModernInk(OriginalInk):
    def __init__(self,display=False):
        super().__init__(display);self.weight=84
    def line(self,points,width=None):
        # 한 윤곽의 양쪽 가장자리를 연결한다. 직선 끝은 평평하게, 모서리는 작은 마이터로 만든다.
        points=[tuple(p) for i,p in enumerate(points) if i==0 or p!=points[i-1]]
        if len(points)<2:return
        closed=len(points)>3 and points[0]==points[-1]
        if closed:points.pop()
        width=width or self.weight
        if len(points)==2 and abs(points[0][1]-points[1][1])<1:width*=.92
        r=width/2;normals=[]
        edges=list(zip(points,points[1:]+([points[0]] if closed else [])))
        for (x,y),(a,b) in edges:
            length=math.hypot(a-x,b-y);normals.append((-(b-y)/length,(a-x)/length))
        left=[];right=[]
        for i,(x,y) in enumerate(points):
            if i==0 and not closed:nx,ny=normals[0];scale=r
            elif i==len(points)-1 and not closed:nx,ny=normals[-1];scale=r
            else:
                ax,ay=normals[i-1];bx,by=normals[i];nx,ny=ax+bx,ay+by
                length=math.hypot(nx,ny)
                if length<.0001:nx,ny=bx,by
                else:nx/=length;ny/=length
                scale=min(r*2.2,r/max(.45,nx*bx+ny*by))
            left.append((x+nx*scale,y+ny*scale));right.append((x-nx*scale,y-ny*scale))
        if closed:
            # 네모의 안쪽을 한 획의 왕복 경로로 연결하지 않고 독립된 구멍으로 만든다.
            area=sum(points[i][0]*points[(i+1)%len(points)][1]-points[(i+1)%len(points)][0]*points[i][1] for i in range(len(points)))
            self.polygon(right if area>0 else left)
            self.polygon(left if area>0 else right,hole=True)
        else:self.polygon(left+right[::-1])
    def oval(self,x,y,rx,ry,width=None):
        # 8개의 이차 곡선으로 부드러운 타원을 만든다. 구멍은 반대 방향이다.
        r=(width or self.weight)/2;dy=r*.92
        assert rx>r and ry>dy,(rx,ry,r)
        def pt(a,xx,yy):return (round(x+xx*math.cos(a)),round(800-(y+yy*math.sin(a))))
        for hole in (False,True):
            xx=rx+(-r if hole else r);yy=ry+(-dy if hole else dy);direction=1 if hole else -1
            self.pen.moveTo(pt(0,xx,yy))
            for i in range(8):
                a=direction*(i+.5)*math.pi/4;b=direction*(i+1)*math.pi/4
                self.pen.qCurveTo(pt(a,xx/math.cos(math.pi/8),yy/math.cos(math.pi/8)),pt(b,xx,yy))
            self.pen.closePath()

def curve(points,commands):
    # 베지어 중심선을 촘촘히 평가해 획을 만든다. 완성 윤곽은 직접 설계한 좌표에서만 생성한다.
    p=list(points)
    for c1,c2,end in commands:
        start=p[-1]
        for i in range(1,17):
            t=i/16;s=1-t
            p.append(tuple(s*s*s*start[k]+3*s*s*t*c1[k]+3*s*t*t*c2[k]+t*t*t*end[k] for k in (0,1)))
    return p

def jamo(ink,char,box):
    x,y,w,h=box
    # 가로 모음 위의 네모 자모를 빈 상자의 폭만큼 늘리지 않는다.
    if char in 'ㅁㅂ' and w>h*1.8:
        narrower=h*1.55;x+=(w-narrower)/2;w=narrower
    # 획 굵기를 중복 축소하지 않는다. 복잡한 작은 칸만 별도 굵기를 적용한다.
    weight=68 if h<330 else 78 if h<450 else 86
    if w<350:weight*=.90
    def line(*p):ink.line([(x+a*w,y+b*h) for a,b in p],weight)
    def oval(a,b,rx,ry):ink.oval(x+a*w,y+b*h,rx*w,ry*h,weight)
    if char in base.PAIRS:
        a,b=base.PAIRS[char]
        jamo(ink,a,(x,y,w*.44,h));jamo(ink,b,(x+w*.56,y,w*.44,h));return
    if char=='ㅎ':
        # 위쪽 짧은 획을 세로로 세우고, 가로획과 아래 원의 비례를 바꾼다.
        line((.50,.00),(.50,.19));line((.12,.19),(.88,.19))
        ink.oval(x+w*.5,y+h*.71,min(w*.29,h*.37),min(h*.225,w*.32),weight)
    elif char=='ㅅ':
        # 정삼각형식 대칭에서 벗어나 두 사선의 출발점과 길이를 조절한다.
        line((.51,.09),(.43,.43),(.10,.89));line((.48,.42),(.88,.88))
    elif char in ('ㅈ','ㅊ'):
        top=.27 if char=='ㅊ' else .10
        if char=='ㅊ':line((.48,.00),(.52,top))
        line((.10,top),(.89,top))
        line((.63,top),(.43,.58),(.10,.90));line((.47,.52),(.89,.89))
    elif char=='ㅇ':
        ink.oval(x+w*.5,y+h*.5,min(w*.35,h*.44),min(h*.36,w*.39),weight)
    elif char=='ㄱ':line((.12,.13),(.87,.13),(.87,.88))
    elif char=='ㄴ':line((.13,.12),(.13,.87),(.88,.87))
    elif char=='ㄷ':line((.87,.13),(.13,.13),(.13,.87),(.87,.87))
    elif char=='ㄹ':line((.13,.08),(.87,.08),(.87,.50),(.13,.50),(.13,.92),(.87,.92))
    elif char=='ㅁ':line((.13,.13),(.87,.13),(.87,.87),(.13,.87),(.13,.13))
    elif char=='ㅂ':
        line((.13,.10),(.13,.88),(.87,.88),(.87,.10));line((.13,.48),(.87,.48))
    elif char=='ㅋ':line((.13,.13),(.87,.13),(.87,.87));line((.13,.50),(.87,.50))
    elif char=='ㅌ':line((.87,.13),(.13,.13),(.13,.87),(.87,.87));line((.13,.50),(.87,.50))
    elif char=='ㅍ':
        line((.10,.13),(.90,.13));line((.10,.87),(.90,.87));line((.29,.13),(.29,.87));line((.71,.13),(.71,.87))
    elif char in 'ㅏㅐㅑㅒㅓㅔㅕㅖㅣ':
        # 두 세로획 사이에 작은 크기에서도 가지가 드러날 공간을 둔다.
        weight=72 if h<600 else 80
        if char=='ㅣ':line((.50,.08),(.50,.92));return
        extra=char in 'ㅐㅒㅔㅖ';right=char in 'ㅏㅐㅑㅒ';double=char in 'ㅑㅒㅕㅖ'
        stem=(.20 if right else .48) if extra else (.30 if right else .70)
        line((stem,.08),(stem,.92))
        for yy in ([.24,.76] if double else [.50]):
            line((stem,yy),((.57 if extra else .90) if right else .08,yy))
        if extra:line((.91,.08),(.91,.92))
    else:
        # 모음의 가지 간격은 이전에 검수한 정의를 사용하되, 보정한 칸과 굵기를 전달한다.
        previous=ink.weight;ink.weight=weight
        original_jamo(ink,char,(x,y,w,h));ink.weight=previous

def syllable(ink,cp):
    n=cp-0xac00;l=base.LEADS[n//588];v=base.VOWELS[n//28%21];t=base.TAILS[n%28]
    # 받침을 상대적으로 낮고 작게 배치하고, 모음 종류별로 초성의 자리를 따로 정한다.
    if v in base.MIXED:
        a,b=base.MIXED[v]
        lead=(90,40 if l=='ㅎ' and t else 95,470,300 if t else 460)
        jamo(ink,l,lead);jamo(ink,a,(65,430 if t else 605,540,190 if t else 260))
        jamo(ink,b,(655,75 if t else 90,275,520 if t else 775))
    elif v in 'ㅗㅛㅜㅠㅡ':
        jamo(ink,l,(155,40 if l=='ㅎ' and t else 95,690,300 if t else 460))
        jamo(ink,v,(65,430 if t else 600,870,190 if t else 265))
    else:
        jamo(ink,l,(70,110 if t else 125,460,440 if t else 655))
        extra=v in 'ㅐㅒㅔㅖ'
        jamo(ink,v,(580 if extra else 615,70 if t else 85,350 if extra else 310,520 if t else 790))
    if t:
        # 하나의 받침과 겹받침의 폭을 구분한다. 원형·네모 받침의 과도한 납작해짐을 피한다.
        widths={'ㄱ':570,'ㄴ':560,'ㄷ':570,'ㄹ':540,'ㅁ':470,'ㅂ':470,'ㅅ':500,'ㅇ':420,
                'ㅈ':540,'ㅊ':540,'ㅋ':560,'ㅌ':560,'ㅍ':560,'ㅎ':450}
        width=widths.get(t,740)
        jamo(ink,t,((1000-width)/2,625,width,290))

def latin(ink,c):
    # 본문에 자주 나오는 곡선 글자와 두 층 a를 별도로 설계한다.
    if c in 'BDPR':
        ink.line([(90,800),(90,110)])
        if c=='D':
            ink.line(curve([(90,110),(285,110)],[((620,110),(620,800),(285,800))])+[(90,800)])
        else:
            ink.line(curve([(90,110),(295,110)],[((595,110),(595,455),(295,455))])+[(90,455)])
            if c=='B':ink.line(curve([(90,455),(310,455)],[((615,455),(615,800),(310,800))])+[(90,800)])
            if c=='R':ink.line([(300,455),(545,800)])
    elif c=='U':ink.line(curve([(90,110),(90,575)],[((90,875),(520,875),(520,575))])+[(520,110)])
    elif c=='J':ink.line(curve([(500,110),(500,600)],[((500,860),(150,890),(85,675))]))
    elif c=='2':
        ink.line(curve([(90,260)],[((130,70),(485,50),(520,260)),((550,420),(220,615),(90,800))])+[(540,800)])
    elif c=='3':
        ink.line(curve([(100,175)],[((300,35),(545,105),(515,280)),((495,415),(355,455),(255,455))]))
        ink.line(curve([(255,455)],[((615,410),(645,815),(335,810)),((230,815),(145,785),(90,715))]))
    elif c=='5':
        ink.line(curve([(515,110),(120,110),(100,425)],[((415,340),(555,490),(525,665)),((490,850),(235,860),(90,730))]))
    elif c=='6':
        ink.line(curve([(495,160)],[((285,35),(95,260),(95,590))]));ink.oval(305,600,210,205)
    elif c=='9':
        ink.oval(305,310,210,205);ink.line(curve([(515,310)],[((535,615),(350,905),(105,750))]))
    elif c=='a':
        ink.line(curve([(110,400)],[((180,310),(385,285),(465,380)),((520,440),(500,620),(505,800))]))
        ink.oval(285,635,207,164)
    elif c=='e':
        ink.line(curve([(515,725)],[((425,830),(185,840),(100,660)),((10,450),(165,280),(345,330)),((460,350),(520,440),(510,550))]))
        ink.line([(95,550),(510,550)])
    elif c=='c':
        ink.line(curve([(510,395)],[((385,275),(165,305),(100,460)),((15,670),(185,890),(505,735))]))
    elif c=='s':
        ink.line(curve([(500,390)],[((360,285),(125,300),(110,430)),((85,575),(495,530),(505,680)),((510,835),(250,860),(95,750))]))
    elif c in 'CG':
        ink.line(curve([(520,220)],[((400,65),(180,75),(90,260)),((0,470),(80,795),(290,800)),((405,805),(490,745),(520,690))]))
        if c=='G':ink.line([(520,690),(520,480),(330,480)])
    elif c=='S':
        ink.line(curve([(520,205)],[((365,55),(100,95),(95,280)),((85,480),(530,400),(530,620)),((530,850),(210,865),(85,715))]))
    elif c in 'bdpq':
        ink.oval(300,560,205,240)
        x=95 if c in 'bp' else 505
        ink.line([(x,110 if c in 'bd' else 320),(x,990 if c in 'pq' else 800)])
    elif c=='g':
        ink.oval(290,550,195,225);ink.line(curve([(495,320)],[((495,530),(510,760),(475,865)),((440,1000),(205,1020),(105,925))]))
    elif c in 'hnmu':
        if c=='h':ink.line([(95,110),(95,800)])
        elif c in 'nm':ink.line([(75 if c=='m' else 95,320),(75 if c=='m' else 95,800)])
        if c in 'hn':ink.line(curve([(95,460)],[((175,275),(480,280),(505,450))])+[(505,800)])
        elif c=='m':
            ink.line(curve([(75,450)],[((135,290),(285,290),(300,430))])+[(300,800)])
            ink.line(curve([(300,430)],[((365,285),(535,290),(550,430))])+[(550,800)])
        else:
            ink.line(curve([(95,320),(95,650)],[((95,850),(370,855),(505,655))]));ink.line([(505,320),(505,800)])
    else:return original_latin(ink,c)
    return 620
