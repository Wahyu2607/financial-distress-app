import zipfile
import xml.etree.ElementTree as ET

ns = {
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
}

p = 'skripsi_research/docs/skripsi/2026-TEMPLATE-PPT-MOVEBEYOND.pptx'
with zipfile.ZipFile(p, 'r') as z:
    for i in range(1, 15):
        sname = f'ppt/slides/slide{i}.xml'
        tree = ET.fromstring(z.read(sname))
        print(f"=== SLIDE {i} SHAPES COORDS ===")
        for sp in tree.findall('.//p:sp', ns) + tree.findall('.//p:pic', ns) + tree.findall('.//p:graphicFrame', ns):
            cNvPr = sp.find('.//p:cNvPr', ns)
            name = cNvPr.get('name') if cNvPr is not None else 'unknown'
            tag = sp.tag.split('}')[-1]
            xfrm = sp.find('.//a:xfrm', ns)
            if xfrm is not None:
                off = xfrm.find('a:off', ns)
                ext = xfrm.find('a:ext', ns)
                ox = off.get('x') if off is not None else '0'
                oy = off.get('y') if off is not None else '0'
                cx = ext.get('cx') if ext is not None else '0'
                cy = ext.get('cy') if ext is not None else '0'
                print(f"  {name} ({tag}): x={ox}, y={oy}, cx={cx}, cy={cy}")
