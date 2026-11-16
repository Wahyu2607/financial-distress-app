import zipfile
import xml.etree.ElementTree as ET

pptx_backup = 'skripsi_research/docs/skripsi/2026-TEMPLATE-PPT-MOVEBEYOND_backup.pptx'

with zipfile.ZipFile(pptx_backup, 'r') as z:
    for layout in ['slideLayout1.xml', 'slideLayout2.xml']:
        root = ET.fromstring(z.read(f'ppt/slideLayouts/{layout}'))
        print(f"=== {layout} ===")
        for sp in root.findall('.//{http://schemas.openxmlformats.org/presentationml/2006/main}sp'):
            name = sp.find('.//{http://schemas.openxmlformats.org/presentationml/2006/main}cNvPr')
            name_str = name.attrib.get('name') if name is not None else ''
            print(f"  Shape: {name_str}")
            for rPr in sp.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}rPr'):
                clrs = [c.attrib.get('val') for c in rPr.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}schemeClr')]
                sclrs = [c.attrib.get('val') for c in rPr.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr')]
                print(f"    rPr scheme: {clrs}, srgb: {sclrs}")
