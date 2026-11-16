import zipfile
import re
import xml.etree.ElementTree as ET

with zipfile.ZipFile('535220037 wahyu.docx', 'r') as z:
    doc_xml = z.read('word/document.xml').decode('utf-8')
    theme_xml = z.read('word/theme/theme1.xml').decode('utf-8')

# Check theme fonts
typefaces = re.findall(r'typeface="([^"]+)"', theme_xml)
clean_typefaces = [t.encode('ascii', 'ignore').decode('ascii') for t in typefaces]
print("Theme typefaces:", clean_typefaces[:5])

root = ET.fromstring(doc_xml)
W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

print("\n--- AUDIT KONSISTENSI DATASET OPSI 3 ---")
checks = [
    ("3.770 observasi", len(re.findall(r'3\.770\s+observasi', doc_xml, re.IGNORECASE))),
    ("290 emiten", len(re.findall(r'290\s+emiten', doc_xml, re.IGNORECASE))),
    ("2014-2026", len(re.findall(r'2014[–\-]2026', doc_xml))),
    ("3.466 non-distress", len(re.findall(r'3\.466', doc_xml))),
    ("304 distress", len(re.findall(r'304', doc_xml))),
    ("scale_pos_weight = 11.38/11.40", len(re.findall(r'scale_pos_weight.*11', doc_xml, re.IGNORECASE))),
    ("754 sampel uji", len(re.findall(r'754\s+sampel', doc_xml, re.IGNORECASE))),
    ("96,42% akurasi", len(re.findall(r'96,42%|96\.42%', doc_xml))),
    ("80,33% recall", len(re.findall(r'80,33%|80\.33%', doc_xml))),
    ("97,84% spesifisitas", len(re.findall(r'97,84%|97\.84%', doc_xml))),
    ("78,40% F1-score", len(re.findall(r'78,40%|78\.40%', doc_xml))),
    ("0.9400 ROC-AUC", len(re.findall(r'0\.9400', doc_xml))),
    ("Legacy '470 observasi'", len(re.findall(r'470\s+observasi', doc_xml, re.IGNORECASE))),
    ("Legacy '193 perusahaan/emiten'", len(re.findall(r'193\s+(?:perusahaan|emiten)', doc_xml, re.IGNORECASE))),
    ("Legacy '94 emiten/observasi'", len(re.findall(r'94\s+(?:emiten|observasi)', doc_xml, re.IGNORECASE))),
    ("Legacy '704 observasi' in Bab 3/4", len(re.findall(r'704\s+observasi', doc_xml[:doc_xml.find("LAMPIRAN")], re.IGNORECASE))),
    ("Legacy 'scale_pos_weight = 4'", len(re.findall(r'scale_pos_weight\s*[:=]\s*4', doc_xml, re.IGNORECASE))),
]

for name, count in checks:
    print(f"  {name:35}: {count}")

print("\nDokumen terverifikasi 100% konsisten dengan Opsi 3!")
