import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile('update4.docx', 'r') as docx:
    xml_content = docx.read('word/document.xml')

root = ET.fromstring(xml_content)
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
body = root.find('w:body', ns)

elements = list(body)
# Table 4.7 is at element 784, Table 4.8 is at element 789
for name, idx in [("Tabel 4.7", 784), ("Tabel 4.8", 789)]:
    tbl = elements[idx]
    tbl_pr = tbl.find('w:tblPr', ns)
    grid = tbl.find('w:tblGrid', ns)
    rows = tbl.findall('w:tr', ns)
    print(f"=== {name} ===")
    print("tblPr:", ET.tostring(tbl_pr, encoding='utf-8').decode('utf-8'))
    print("grid:", ET.tostring(grid, encoding='utf-8').decode('utf-8'))
    print(f"Num rows: {len(rows)}")
    header_tr = rows[0]
    print("Header row XML snippet:", ET.tostring(header_tr, encoding='utf-8').decode('utf-8')[:600])
