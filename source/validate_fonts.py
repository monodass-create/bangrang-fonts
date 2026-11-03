"""파일·전체 한글 조합·의도하지 않은 자모 접촉을 검사한다. 가독성 판단은 별도다."""
from pathlib import Path
import json,hashlib,struct
from fontTools.ttLib import TTFont
from fontTools.ttLib.removeOverlaps import skPathFromGlyph
import legacy_v03 as base
ROOT=Path(__file__).resolve().parents[1]
def parts(ch):
    if not ch:return 0
    if ch in base.PAIRS:return sum(parts(c) for c in base.PAIRS[ch])
    if ch in base.MIXED:return sum(parts(c) for c in base.MIXED[ch])
    return 2 if ch in 'ㅎㅐㅒㅔㅖ' else 1

results=[];failures=[]
for path in sorted((ROOT/'fonts').glob('*.ttf')):
    f=TTFont(path,checkChecksums=2)
    for tag in f.reader.keys():f.reader[tag];f[tag]
    cm=f.getBestCmap();glyf=f['glyf'];metrics=f['hmtx'];seen={};bounds=[]
    for cp in range(0xac00,0xd7a4):
        assert cp in cm;g=glyf[cm[cp]];assert g.numberOfContours>0
        digest=hashlib.sha256(g.compile(glyf)).hexdigest();assert digest not in seen,(cp,seen.get(digest));seen[digest]=cp
    assert all(cp in cm for cp in range(32,127))
    assert len({metrics[cm[ord(ch)]][0] for ch in '0123456789'})==1
    assert metrics[cm[ord('W')]][0]>metrics[cm[ord('i')]][0]
    for group in ("'‘’`",'"“”','-–—','Il1','O0'):
        assert len({hashlib.sha256(glyf[cm[ord(c)]].compile(glyf)).hexdigest() for c in group})==len(group)
    for name in f.getGlyphOrder():
        g=glyf[name]
        if g.numberOfContours:
            assert g.xMin>=0 and g.xMax<=metrics[name][0],name
            assert g.yMax<=f['OS/2'].usWinAscent and g.yMin>=-f['OS/2'].usWinDescent,(name,g.yMin,g.yMax)
            bounds.append([g.xMin,g.yMin,g.xMax,g.yMax])
    assert 'GPOS' in f and abs(f['head'].fontRevision-.4)<.00001 and f['name'].getDebugName(5)=='Version 0.400'
    raw=path.read_bytes();pad=raw+b'\0'*((-len(raw))%4)
    assert sum(struct.unpack('>'+str(len(pad)//4)+'I',pad))&0xffffffff==0xb1b0afba
    topology=[]
    if 'UI-' in path.name:
        gs=f.getGlyphSet()
        for cp in range(0xac00,0xd7a4):
            n=cp-0xac00;l=base.LEADS[n//588];v=base.VOWELS[n//28%21];t=base.TAILS[n%28]
            expected=parts(l)+parts(v)+parts(t)
            p=skPathFromGlyph(cm[cp],gs)
            actual=sum(1 for c in p.contours if c.clockwise==p.clockwise)
            if actual!=expected:topology.append({'char':chr(cp),'jamo':l+v+t,'expected_parts':expected,'actual_parts':actual})
        failures.extend(topology)
    results.append({'font':path.name,'sha256':hashlib.sha256(raw).hexdigest(),'hangul_nonempty_distinct':11172,
        'structure_bounds_metadata_checksum':'passed','topology_tested':11172 if 'UI-' in path.name else 0,
        'topology_mismatches':topology,'limits':'Structural validation; not human readability certification'})
(ROOT/'regression-validation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Topology mismatches:',len(failures),json.dumps(failures[:12],ensure_ascii=True),flush=True)
assert not failures,'Unexpected joined or separated Hangul components'
