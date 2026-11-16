import os
import shutil
import zipfile
import xml.etree.ElementTree as ET

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"

namespaces = {
    'w': W_NS,
    'r': "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    'm': "http://schemas.openxmlformats.org/officeDocument/2006/math",
    'mc': "http://schemas.openxmlformats.org/markup-compatibility/2006",
    'w14': "http://schemas.microsoft.com/office/word/2010/wordml",
    'w15': "http://schemas.microsoft.com/office/word/2012/wordml",
}

for prefix, uri in namespaces.items():
    ET.register_namespace(prefix, uri)

def update_rfonts_to_calibri(rf):
    changed = False
    ascii_val = rf.get(f"{{{W_NS}}}ascii", "")
    hAnsi_val = rf.get(f"{{{W_NS}}}hAnsi", "")
    cs_val = rf.get(f"{{{W_NS}}}cs", "")
    eastAsia_val = rf.get(f"{{{W_NS}}}eastAsia", "")
    
    # Preserve Consolas (for code blocks) and Cambria Math (for math formulas)
    if "Consolas" in ascii_val or "Cambria Math" in ascii_val:
        return False
        
    if "Times" in ascii_val or "Times" in hAnsi_val or "Times" in cs_val or "Times" in eastAsia_val:
        rf.set(f"{{{W_NS}}}ascii", "Calibri")
        rf.set(f"{{{W_NS}}}hAnsi", "Calibri")
        rf.set(f"{{{W_NS}}}cs", "Calibri")
        rf.set(f"{{{W_NS}}}cstheme", "minorHAnsi")
        rf.set(f"{{{W_NS}}}asciiTheme", "minorHAnsi")
        rf.set(f"{{{W_NS}}}hAnsiTheme", "minorHAnsi")
        if f"{{{W_NS}}}eastAsia" in rf.attrib:
            del rf.attrib[f"{{{W_NS}}}eastAsia"]
        changed = True
        
    return changed

def process_document_xml(xml_content):
    tree = ET.fromstring(xml_content)
    body = tree.find(f"{{{W_NS}}}body")
    
    fonts_changed = 0
    spacing_changed = 0
    
    # 1. Update all rFonts in the entire document (paragraphs, runs, tables)
    for rf in tree.iter(f"{{{W_NS}}}rFonts"):
        if update_rfonts_to_calibri(rf):
            fonts_changed += 1
            
    # 2. Update line and paragraph spacing for narrative / body paragraphs
    for idx, el in enumerate(body):
        if el.tag == f"{{{W_NS}}}p":
            pPr = el.find(f"{{{W_NS}}}pPr")
            if pPr is None:
                continue
                
            pStyle = pPr.find(f"{{{W_NS}}}pStyle")
            style_val = pStyle.get(f"{{{W_NS}}}val") if pStyle is not None else ""
            
            # Check if this paragraph is a body narrative paragraph
            sp = pPr.find(f"{{{W_NS}}}spacing")
            
            # Headings: ensure line=480 (2.0 line spacing)
            if "heading" in style_val.lower():
                if sp is None:
                    sp = ET.SubElement(pPr, f"{{{W_NS}}}spacing")
                sp.set(f"{{{W_NS}}}line", "480")
                sp.set(f"{{{W_NS}}}lineRule", "auto")
                spacing_changed += 1
            elif style_val == "paragraf" or (sp is not None and sp.get(f"{{{W_NS}}}line") in ["360", "480"]):
                # Narrative body paragraph
                if sp is None:
                    sp = ET.SubElement(pPr, f"{{{W_NS}}}spacing")
                    
                sp.set(f"{{{W_NS}}}line", "480")
                sp.set(f"{{{W_NS}}}lineRule", "auto")
                
                # Normalize paragraph spacing (remove artificial after=60 or after=30 from 1.5 spacing)
                if f"{{{W_NS}}}after" in sp.attrib and sp.attrib[f"{{{W_NS}}}after"] in ["60", "30", "40"]:
                    sp.attrib[f"{{{W_NS}}}after"] = "0"
                if f"{{{W_NS}}}before" in sp.attrib and sp.attrib[f"{{{W_NS}}}before"] in ["0"]:
                    del sp.attrib[f"{{{W_NS}}}before"]
                    
                spacing_changed += 1
                
    return ET.tostring(tree, encoding="utf-8", xml_declaration=True), fonts_changed, spacing_changed

def process_styles_xml(xml_content):
    tree = ET.fromstring(xml_content)
    changed = False
    
    for s in tree.findall(f"{{{W_NS}}}style"):
        s_id = s.get(f"{{{W_NS}}}styleId", "")
        
        # Headings: set line spacing to 480
        if "heading" in s_id.lower():
            pPr = s.find(f"{{{W_NS}}}pPr")
            if pPr is not None:
                sp = pPr.find(f"{{{W_NS}}}spacing")
                if sp is not None:
                    sp.set(f"{{{W_NS}}}line", "480")
                    sp.set(f"{{{W_NS}}}lineRule", "auto")
                    changed = True
                    
        # Update any rFonts in styles
        for rf in s.iter(f"{{{W_NS}}}rFonts"):
            if update_rfonts_to_calibri(rf):
                changed = True
                
    return ET.tostring(tree, encoding="utf-8", xml_declaration=True), changed

def main():
    target_docx = "535220037 wahyu.docx"
    backup_docx = "535220037 wahyu_backup_before_calibri.docx"
    
    print(f"Membuat backup berkas: {backup_docx} ...")
    shutil.copyfile(target_docx, backup_docx)
    
    with zipfile.ZipFile(target_docx, 'r') as zin:
        all_files = {name: zin.read(name) for name in zin.namelist()}
        
    print("Memproses word/document.xml ...")
    doc_xml = all_files["word/document.xml"]
    new_doc_xml, fonts_changed, spacing_changed = process_document_xml(doc_xml)
    all_files["word/document.xml"] = new_doc_xml
    print(f" -> rFonts diubah ke Calibri: {fonts_changed}")
    print(f" -> Paragraf disesuaikan ke line=480 (2.0 spasi): {spacing_changed}")
    
    if "word/styles.xml" in all_files:
        print("Memproses word/styles.xml ...")
        styles_xml = all_files["word/styles.xml"]
        new_styles_xml, s_changed = process_styles_xml(styles_xml)
        all_files["word/styles.xml"] = new_styles_xml
        print(f" -> styles.xml updated: {s_changed}")
        
    # Process footers / footnotes if any
    for name in list(all_files.keys()):
        if (name.startswith("word/footer") or name.startswith("word/header") or name.startswith("word/footnote") or name.startswith("word/glossary")) and name.endswith(".xml"):
            f_xml = all_files[name]
            f_tree = ET.fromstring(f_xml)
            f_changed = False
            for rf in f_tree.iter(f"{{{W_NS}}}rFonts"):
                if update_rfonts_to_calibri(rf):
                    f_changed = True
            if f_changed:
                all_files[name] = ET.tostring(f_tree, encoding="utf-8", xml_declaration=True)
                print(f" -> Updated fonts in {name}")
                
    temp_docx = "535220037 wahyu_calibri_temp.docx"
    with zipfile.ZipFile(temp_docx, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
        for name, content in all_files.items():
            zout.writestr(name, content)
            
    shutil.copyfile(temp_docx, target_docx)
    os.remove(temp_docx)
    print("Sukses mengubah font ke Calibri Body dan spasi ke 2.0 di seluruh dokumen!")

if __name__ == "__main__":
    main()
