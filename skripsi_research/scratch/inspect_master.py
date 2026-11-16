import zipfile
import xml.etree.ElementTree as ET

pptx_backup = 'skripsi_research/docs/skripsi/2026-TEMPLATE-PPT-MOVEBEYOND_backup.pptx'

with zipfile.ZipFile(pptx_backup, 'r') as z:
    root = ET.fromstring(z.read('ppt/slideMasters/slideMaster1.xml'))
    print("=== slideMaster1.xml txStyles ===")
    txStyles = root.find('{http://schemas.openxmlformats.org/presentationml/2006/main}txStyles')
    for style_type in ['titleStyle', 'bodyStyle', 'otherStyle']:
        elem = txStyles.find(f'{{http://schemas.openxmlformats.org/presentationml/2006/main}}{style_type}')
        if elem is not None:
            print(f"-- {style_type} --")
            for lvl in elem:
                lvl_name = lvl.tag.split('}')[-1]
                defRPr = lvl.find('{http://schemas.openxmlformats.org/drawingml/2006/main}defRPr')
                if defRPr is not None:
                    clrs = [c.attrib.get('val') for c in defRPr.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}schemeClr')]
                    sclrs = [c.attrib.get('val') for c in defRPr.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr')]
                    print(f"  {lvl_name}: scheme={clrs}, srgb={sclrs}, sz={defRPr.attrib.get('sz')}")
