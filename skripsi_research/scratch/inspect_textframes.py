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
        print(f"\n==================== SLIDE {i} ====================")
        for sp in tree.findall('.//p:sp', ns):
            name = sp.find('.//p:cNvPr', ns).get('name')
            txBody = sp.find('.//p:txBody', ns)
            if txBody is not None:
                paras = txBody.findall('a:p', ns)
                print(f"  Shape [{name}] with {len(paras)} paragraphs:")
                for p_idx, para in enumerate(paras):
                    runs = para.findall('a:r', ns)
                    fld = para.find('a:fld', ns)
                    text = "".join([r.find('a:t', ns).text for r in runs if r.find('a:t', ns) is not None and r.find('a:t', ns).text])
                    if fld is not None:
                        t = fld.find('a:t', ns)
                        if t is not None and t.text:
                            text += " [FLD: " + t.text + "]"
                    print(f"    P{p_idx}: {text}")
