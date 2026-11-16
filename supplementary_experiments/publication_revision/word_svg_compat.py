"""Normalize Matplotlib SVG for Word without changing points or drawing order.

Expands CSS font shorthand and combines consecutive identically styled scatter
paths. Original publication SVGs remain untouched. Coordinate precision is
three decimal points (maximum displacement 0.0005 typographic point).
"""
import re
from copy import deepcopy
from lxml import etree as E

S='http://www.w3.org/2000/svg'
X='http://www.w3.org/1999/xlink'
num=re.compile(r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?')

def compact_path(d,dx=0,dy=0):
    # Matplotlib marker paths use absolute M, L and C commands only.
    assert not re.search(r'[a-yA-BD-KN-Y]',num.sub('',d)), d[:80]
    count=0
    def sub(m):
        nonlocal count
        v=float(m.group())+(dx if count%2==0 else dy);count+=1
        return f'{v:.3f}'.rstrip('0').rstrip('.') if abs(v)>=.0005 else '0'
    return re.sub(r'\s+',' ',num.sub(sub,d)).strip()

def normalize(source,target):
    tree=E.parse(str(source),E.XMLParser(remove_blank_text=True))
    root=tree.getroot(); refs={e.get('id'):e for e in root.iter() if e.get('id')}
    for e in root.iter('{'+S+'}text'):
        style=e.get('style','')
        match=re.search(r'font:\s*([^;]+)',style)
        if match:
            font=match.group(1);size=re.search(r'([\d.]+)px',font)
            if size:
                e.set('font-size',size.group(1));e.set('font-family','Arial')
                e.set('font-weight','bold' if 'bold' in font or '700' in font else 'normal')
                if 'italic' in font:e.set('font-style','italic')
                style=style.replace(match.group(0),'')
        e.set('style',style.strip('; '))
    for group in list(root.iter('{'+S+'}g')):
        if not group.get('id','').startswith(('PathCollection','EllipseCollection')):continue
        previous=None;previous_key=None
        for child in list(group):
            candidate=child
            clip=child.get('clip-path')
            if child.tag=='{'+S+'}g' and len(child)==1 and child[0].tag=='{'+S+'}use':
                candidate=child[0]
            if candidate.tag=='{'+S+'}use':
                ref=refs[candidate.get('{'+X+'}href')[1:]]
                if ref.tag!='{'+S+'}path':previous=None;continue
                d=compact_path(ref.get('d'),float(candidate.get('x','0')),float(candidate.get('y','0')))
                style=ref.get('style','')+';'+candidate.get('style','')
                path=E.Element('{'+S+'}path',d=d,style=style.strip(';'))
                if clip:path.set('clip-path',clip)
                group.replace(child,path)
            elif candidate.tag=='{'+S+'}path' and not candidate.get('transform'):
                path=candidate;path.set('d',compact_path(path.get('d')))
            else:previous=None;previous_key=None;continue
            key=(path.get('style'),path.get('clip-path'))
            if previous is not None and key==previous_key:
                previous.set('d',previous.get('d')+' '+path.get('d'));group.remove(path)
            else:previous=path;previous_key=key
    # Avoid thousands of redundant IDs and metadata while retaining references.
    for e in list(root):
        if e.tag=='{'+S+'}metadata':root.remove(e)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(E.tostring(root,xml_declaration=True,encoding='utf-8'))
    return target

def spatial_tiles(svg,png):
    """Six full-width strips avoid Word's per-image SVG complexity ceiling."""
    from PIL import Image
    tree=E.parse(str(svg));root=tree.getroot()
    width,height=map(float,root.get('viewBox').split()[2:])
    axes=root.xpath('.//s:g[starts-with(@id,"axes_")]',namespaces={'s':S})
    refs={e.get('id'):e for e in root.iter() if e.get('id')}
    ends=[]
    for ax in axes[:15:3]:
        clip=next(e.get('clip-path')[5:-1] for e in ax.iter() if e.get('clip-path'))
        rect=refs[clip][0];ends.append(float(rect.get('y'))+float(rect.get('height'))+2)
    boundaries=[0]+ends+[height];answer=[]
    with Image.open(png) as preview:
        for i,(top,bottom) in enumerate(zip(boundaries,boundaries[1:])):
            tile=deepcopy(root)
            keep=set(range(i*3+1,i*3+4)) if i<5 else {16}
            for ax in tile.xpath('.//s:g[starts-with(@id,"axes_")]',namespaces={'s':S}):
                if int(ax.get('id').split('_')[-1]) not in keep:ax.getparent().remove(ax)
            tile.set('viewBox',f'0 {top} {width} {bottom-top}')
            tile.set('width',f'{width}pt');tile.set('height',f'{bottom-top}pt')
            tile.set('overflow','hidden')
            target=svg.with_name(svg.stem+f'_strip{i+1}.svg')
            target.write_bytes(E.tostring(tile,encoding='utf-8',xml_declaration=True))
            image=target.with_suffix('.png')
            preview.crop((0,round(top/height*preview.height),preview.width,round(bottom/height*preview.height))).save(image)
            answer.append((target,image,(bottom-top)/height))
    return answer

def pad_left(svg,png,points=12):
    """Add visual breathing room for long labels in Word's font metrics."""
    from PIL import Image,ImageOps
    root=E.parse(str(svg)).getroot()
    x,y,w,h=map(float,root.get('viewBox').split())
    root.set('viewBox',f'{x} {y} {w+points} {h}')
    root.set('width',f'{w+points}pt')
    group=E.Element('{'+S+'}g',transform=f'translate({points},0)')
    for child in list(root):
        if child.tag not in {'{'+S+'}defs','{'+S+'}metadata'}:group.append(child)
    root.append(group)
    target=svg.with_name(svg.stem+'_padded.svg')
    target.write_bytes(E.tostring(root,encoding='utf-8',xml_declaration=True))
    preview=target.with_suffix('.png')
    with Image.open(png) as im:ImageOps.expand(im,border=(round(im.width*points/w),0,0,0),fill='white').save(preview)
    return target,preview
