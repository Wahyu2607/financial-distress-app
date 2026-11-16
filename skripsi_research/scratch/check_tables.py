import zipfile
import xml.etree.ElementTree as ET

ns = {
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
}

p = 'skripsi_research/docs/skripsi/2026-TEMPLATE-PPT-MOVEBEYOND.pptx'
with zipfile.ZipFile(p, 'r') as z:
    for sidx in [7, 10, 13]:
        sname = f'ppt/slides/slide{sidx}.xml'
        tree = ET.fromstring(z.read(sname))
        for gf in tree.findall('.//p:graphicFrame', ns):
            xfrm = gf.find('.//p:xfrm', ns)
            off = xfrm.find('a:off', ns)
            ext = xfrm.find('a:ext', ns)
            name = gf.find('.//p:cNvPr', ns).get('name')
            print(f"Slide {sidx} {name}: x={off.get('x')}, y={off.get('y')}, cx={ext.get('cx')}, cy={ext.get('cy')}")
            tbl = gf.find('.//a:tbl', ns)
            if tbl is not None:
                rows = tbl.findall('a:tr', ns)
                print(f"  Table rows: {len(rows)}")
                for r_idx, row in enumerate(rows):
                    cells = [ "".join([t.text for t in cell.findall('.//a:t', ns) if t.text]).strip() for cell in row.findall('a:tc', ns) ]
                    print(f"    Row {r_idx}: {cells}")
