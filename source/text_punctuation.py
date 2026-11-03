"""장문 기록지의 괄호·제목 부호를 직접 만든다. 외부 윤곽은 읽지 않는다."""
import legacy_v03 as base
import ui_shapes as shapes

ADDED='「」『』〈〉《》※'

def draw(char,display=False):
    ink=shapes.OriginalInk(True) if display else shapes.ModernInk()
    weight=66 if display else 64
    closing=char in '」』〉》)'
    def points(values,advance):
        # 닫는 낫표는 좌우 반사만 하면 위쪽 모서리가 남는다. 아래 모서리로 회전한다.
        if char in '」』':return [(advance-x,805-y) for x,y in values]
        return [(advance-x,y) for x,y in values] if closing else values
    def line(values,advance):ink.line(points(values,advance),weight)
    if char in '「」『』':
        advance=600
        line([(455,-65),(145,-65),(145,870)],advance)
        if char in '『』':line([(455,55),(265,55),(265,870)],advance)
    elif char in '〈〉《》':
        double=char in '《》';advance=720 if double else 540
        line([(410,-65),(130,400),(410,870)],advance)
        if double:line([(590,-65),(310,400),(590,870)],advance)
    elif char=='※':
        advance=850
        for p in [[(160,135),(690,665)],[(160,665),(690,135)]]:ink.line(p,weight*.8)
        for x,y in [(425,95),(425,705),(120,400),(730,400)]:ink.disk(x,y,40)
    elif char in '()':
        advance=450
        values=shapes.curve([(340,35)],[((65,220),(65,650),(340,850))])
        line(values,advance)
    else:raise ValueError(char)
    glyph=ink.glyph();return glyph,advance

def refine(font,display=False):
    order=font.getGlyphOrder()
    # 괄호 곡선은 UI체만 수정한다. 기록체의 기존 문자는 보존한다.
    chars=ADDED+('()' if not display else '')
    for char in chars:
        cp=ord(char);name=f'uni{cp:04X}';glyph,advance=draw(char,display)
        font['glyf'][name]=glyph;glyph.recalcBounds(font['glyf'])
        font['hmtx'][name]=(advance,glyph.xMin)
        if name not in order:order.append(name)
        for table in font['cmap'].tables:
            if table.isUnicode():table.cmap[cp]=name
    font.setGlyphOrder(order)
    if not display:
        # 글자 사이와 어절 사이를 구별하도록 공백만 늘린다. 한글 윤곽·자폭은 보존한다.
        for cp in (0x20,0xa0):font['hmtx'][font.getBestCmap()[cp]]=(380,0)
