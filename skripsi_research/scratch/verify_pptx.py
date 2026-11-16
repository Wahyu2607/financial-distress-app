import zipfile
import xml.etree.ElementTree as ET

pptx_path = 'skripsi_research/docs/skripsi/2026-TEMPLATE-PPT-MOVEBEYOND.pptx'

with zipfile.ZipFile(pptx_path, 'r') as z:
    for i in range(1, 15):
        name = f'ppt/slides/slide{i}.xml'
        data = z.read(name)
        root = ET.fromstring(data)
        
        texts = [elem.text.strip() for elem in root.iter() if elem.text and elem.text.strip()]
        
        fonts = set()
        for rPr in root.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}rPr'):
            for child in rPr:
                if child.tag.endswith('latin') or child.tag.endswith('cs') or child.tag.endswith('ea'):
                    tf = child.attrib.get('typeface')
                    if tf:
                        fonts.add(tf)
        
        preview = " | ".join(texts[:3])
        print(f"Slide {i:2d}: {len(texts):3d} text runs | Fonts: {list(fonts)} | Preview: {preview[:80]}...")
