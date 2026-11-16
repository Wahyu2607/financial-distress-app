import zipfile
import xml.etree.ElementTree as ET

ns = {
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
}

p = 'skripsi_research/docs/skripsi/2026-TEMPLATE-PPT-MOVEBEYOND.pptx'
with zipfile.ZipFile(p, 'r') as z:
    for i in range(1, 15):
        sname = f'ppt/slides/slide{i}.xml'
        rname = f'ppt/slides/_rels/slide{i}.xml.rels'
        tree = ET.fromstring(z.read(sname))
        rtree = ET.fromstring(z.read(rname)) if rname in z.namelist() else None
        rel_map = {}
        if rtree is not None:
            for rel in rtree.findall('{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'):
                rel_map[rel.get('Id')] = rel.get('Target')

        print(f"==================== SLIDE {i} ====================")
        sp_tree = tree.find('.//p:spTree', ns)
        if sp_tree is not None:
            for child in sp_tree:
                tag = child.tag.split('}')[-1]
                cNvPr = child.find('.//p:cNvPr', ns)
                name = cNvPr.get('name') if cNvPr is not None else 'unknown'
                blip = child.find('.//a:blip', ns)
                embed_id = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed') if blip is not None else None
                target = rel_map.get(embed_id, '') if embed_id else ''
                
                # Extract text
                texts = []
                for p_elem in child.findall('.//a:p', ns):
                    line = ''.join([t.text for t in p_elem.findall('.//a:t', ns) if t.text])
                    if line:
                        texts.append(line)
                
                print(f"  [{tag}] {name} (embed: {target})")
                for t in texts:
                    print(f"      {t}")
