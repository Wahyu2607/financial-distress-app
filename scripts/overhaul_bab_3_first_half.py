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

def create_heading3(text):
    p = ET.Element(f"{{{W_NS}}}p")
    pPr = ET.SubElement(p, f"{{{W_NS}}}pPr")
    pStyle = ET.SubElement(pPr, f"{{{W_NS}}}pStyle")
    pStyle.set(f"{{{W_NS}}}val", "heading30")
    numPr = ET.SubElement(pPr, f"{{{W_NS}}}numPr")
    ilvl = ET.SubElement(numPr, f"{{{W_NS}}}ilvl")
    ilvl.set(f"{{{W_NS}}}val", "0")
    numId = ET.SubElement(numPr, f"{{{W_NS}}}numId")
    numId.set(f"{{{W_NS}}}val", "36")
    spacing = ET.SubElement(pPr, f"{{{W_NS}}}spacing")
    spacing.set(f"{{{W_NS}}}line", "480")
    spacing.set(f"{{{W_NS}}}lineRule", "auto")
    spacing.set(f"{{{W_NS}}}before", "140")
    spacing.set(f"{{{W_NS}}}after", "70")
    rPr_p = ET.SubElement(pPr, f"{{{W_NS}}}rPr")
    rFonts_p = ET.SubElement(rPr_p, f"{{{W_NS}}}rFonts")
    rFonts_p.set(f"{{{W_NS}}}ascii", "Times New Roman")
    rFonts_p.set(f"{{{W_NS}}}hAnsi", "Times New Roman")
    b_p = ET.SubElement(rPr_p, f"{{{W_NS}}}b")
    sz_p = ET.SubElement(rPr_p, f"{{{W_NS}}}sz")
    sz_p.set(f"{{{W_NS}}}val", "24")
    
    r = ET.SubElement(p, f"{{{W_NS}}}r")
    rPr = ET.SubElement(r, f"{{{W_NS}}}rPr")
    rFonts = ET.SubElement(rPr, f"{{{W_NS}}}rFonts")
    rFonts.set(f"{{{W_NS}}}ascii", "Times New Roman")
    rFonts.set(f"{{{W_NS}}}hAnsi", "Times New Roman")
    b = ET.SubElement(rPr, f"{{{W_NS}}}b")
    sz = ET.SubElement(rPr, f"{{{W_NS}}}sz")
    sz.set(f"{{{W_NS}}}val", "24")
    t = ET.SubElement(r, f"{{{W_NS}}}t")
    t.set(f"{{{XML_NS}}}space", "preserve")
    t.text = text
    return p

def create_p(text, style="paragraf"):
    p = ET.Element(f"{{{W_NS}}}p")
    pPr = ET.SubElement(p, f"{{{W_NS}}}pPr")
    if style:
        pStyle = ET.SubElement(pPr, f"{{{W_NS}}}pStyle")
        pStyle.set(f"{{{W_NS}}}val", style)
    
    spacing = ET.SubElement(pPr, f"{{{W_NS}}}spacing")
    spacing.set(f"{{{W_NS}}}line", "360") # 1.5 spasi
    spacing.set(f"{{{W_NS}}}lineRule", "auto")
    spacing.set(f"{{{W_NS}}}before", "0")
    spacing.set(f"{{{W_NS}}}after", "60")
    
    jc = ET.SubElement(pPr, f"{{{W_NS}}}jc")
    jc.set(f"{{{W_NS}}}val", "both")
    
    rPr_p = ET.SubElement(pPr, f"{{{W_NS}}}rPr")
    rFonts_p = ET.SubElement(rPr_p, f"{{{W_NS}}}rFonts")
    rFonts_p.set(f"{{{W_NS}}}ascii", "Times New Roman")
    rFonts_p.set(f"{{{W_NS}}}hAnsi", "Times New Roman")
    sz_p = ET.SubElement(rPr_p, f"{{{W_NS}}}sz")
    sz_p.set(f"{{{W_NS}}}val", "24") # 12pt
    
    r = ET.SubElement(p, f"{{{W_NS}}}r")
    rPr = ET.SubElement(r, f"{{{W_NS}}}rPr")
    rFonts = ET.SubElement(rPr, f"{{{W_NS}}}rFonts")
    rFonts.set(f"{{{W_NS}}}ascii", "Times New Roman")
    rFonts.set(f"{{{W_NS}}}hAnsi", "Times New Roman")
    sz = ET.SubElement(rPr, f"{{{W_NS}}}sz")
    sz.set(f"{{{W_NS}}}val", "24")
    t = ET.SubElement(r, f"{{{W_NS}}}t")
    t.set(f"{{{XML_NS}}}space", "preserve")
    t.text = text
    return p

def create_caption(text):
    p = ET.Element(f"{{{W_NS}}}p")
    pPr = ET.SubElement(p, f"{{{W_NS}}}pPr")
    pStyle = ET.SubElement(pPr, f"{{{W_NS}}}pStyle")
    pStyle.set(f"{{{W_NS}}}val", "Caption")
    jc = ET.SubElement(pPr, f"{{{W_NS}}}jc")
    jc.set(f"{{{W_NS}}}val", "center")
    spacing = ET.SubElement(pPr, f"{{{W_NS}}}spacing")
    spacing.set(f"{{{W_NS}}}line", "260")
    spacing.set(f"{{{W_NS}}}before", "140")
    spacing.set(f"{{{W_NS}}}after", "70")
    
    rPr_p = ET.SubElement(pPr, f"{{{W_NS}}}rPr")
    rFonts_p = ET.SubElement(rPr_p, f"{{{W_NS}}}rFonts")
    rFonts_p.set(f"{{{W_NS}}}ascii", "Times New Roman")
    rFonts_p.set(f"{{{W_NS}}}hAnsi", "Times New Roman")
    b_p = ET.SubElement(rPr_p, f"{{{W_NS}}}b")
    sz_p = ET.SubElement(rPr_p, f"{{{W_NS}}}sz")
    sz_p.set(f"{{{W_NS}}}val", "22") # 11pt
    
    r = ET.SubElement(p, f"{{{W_NS}}}r")
    rPr = ET.SubElement(r, f"{{{W_NS}}}rPr")
    rFonts = ET.SubElement(rPr, f"{{{W_NS}}}rFonts")
    rFonts.set(f"{{{W_NS}}}ascii", "Times New Roman")
    rFonts.set(f"{{{W_NS}}}hAnsi", "Times New Roman")
    b = ET.SubElement(rPr, f"{{{W_NS}}}b")
    sz = ET.SubElement(rPr, f"{{{W_NS}}}sz")
    sz.set(f"{{{W_NS}}}val", "22")
    t = ET.SubElement(r, f"{{{W_NS}}}t")
    t.set(f"{{{XML_NS}}}space", "preserve")
    t.text = text
    return p

def create_code_block(code_lines, fill_color="F8FAFC", border_color="CBD5E1", text_color="0F172A"):
    tbl = ET.Element(f"{{{W_NS}}}tbl")
    tblPr = ET.SubElement(tbl, f"{{{W_NS}}}tblPr")
    tblStyle = ET.SubElement(tblPr, f"{{{W_NS}}}tblStyle")
    tblStyle.set(f"{{{W_NS}}}val", "TableGrid")
    tblW = ET.SubElement(tblPr, f"{{{W_NS}}}tblW")
    tblW.set(f"{{{W_NS}}}w", "8500")
    tblW.set(f"{{{W_NS}}}type", "dxa")
    jc = ET.SubElement(tblPr, f"{{{W_NS}}}jc")
    jc.set(f"{{{W_NS}}}val", "center")
    
    tblBorders = ET.SubElement(tblPr, f"{{{W_NS}}}tblBorders")
    for b_name in ["top", "left", "bottom", "right"]:
        b = ET.SubElement(tblBorders, f"{{{W_NS}}}{b_name}")
        b.set(f"{{{W_NS}}}val", "single")
        b.set(f"{{{W_NS}}}sz", "4")
        b.set(f"{{{W_NS}}}space", "0")
        b.set(f"{{{W_NS}}}color", border_color)
    
    tblGrid = ET.SubElement(tbl, f"{{{W_NS}}}tblGrid")
    gridCol = ET.SubElement(tblGrid, f"{{{W_NS}}}gridCol")
    gridCol.set(f"{{{W_NS}}}w", "8500")
    
    tr = ET.SubElement(tbl, f"{{{W_NS}}}tr")
    tc = ET.SubElement(tr, f"{{{W_NS}}}tc")
    tcPr = ET.SubElement(tc, f"{{{W_NS}}}tcPr")
    tcW = ET.SubElement(tcPr, f"{{{W_NS}}}tcW")
    tcW.set(f"{{{W_NS}}}w", "8500")
    tcW.set(f"{{{W_NS}}}type", "dxa")
    shd = ET.SubElement(tcPr, f"{{{W_NS}}}shd")
    shd.set(f"{{{W_NS}}}val", "clear")
    shd.set(f"{{{W_NS}}}color", "auto")
    shd.set(f"{{{W_NS}}}fill", fill_color)
    
    tcMar = ET.SubElement(tcPr, f"{{{W_NS}}}tcMar")
    for m, val in [("top", "120"), ("bottom", "120"), ("left", "180"), ("right", "180")]:
        node = ET.SubElement(tcMar, f"{{{W_NS}}}{m}")
        node.set(f"{{{W_NS}}}w", val)
        node.set(f"{{{W_NS}}}type", "dxa")
        
    for line in code_lines:
        p = ET.SubElement(tc, f"{{{W_NS}}}p")
        pPr = ET.SubElement(p, f"{{{W_NS}}}pPr")
        spacing = ET.SubElement(pPr, f"{{{W_NS}}}spacing")
        spacing.set(f"{{{W_NS}}}line", "220")
        spacing.set(f"{{{W_NS}}}lineRule", "auto")
        spacing.set(f"{{{W_NS}}}before", "0")
        spacing.set(f"{{{W_NS}}}after", "0")
        r = ET.SubElement(p, f"{{{W_NS}}}r")
        rPr = ET.SubElement(r, f"{{{W_NS}}}rPr")
        rFonts = ET.SubElement(rPr, f"{{{W_NS}}}rFonts")
        rFonts.set(f"{{{W_NS}}}ascii", "Consolas")
        rFonts.set(f"{{{W_NS}}}hAnsi", "Consolas")
        sz = ET.SubElement(rPr, f"{{{W_NS}}}sz")
        sz.set(f"{{{W_NS}}}val", "18")  # 9pt
        color = ET.SubElement(rPr, f"{{{W_NS}}}color")
        color.set(f"{{{W_NS}}}val", text_color)
        t = ET.SubElement(r, f"{{{W_NS}}}t")
        t.set(f"{{{XML_NS}}}space", "preserve")
        t.text = line
        
    return tbl

def create_table(headers, rows, widths=None):
    tbl = ET.Element(f"{{{W_NS}}}tbl")
    tblPr = ET.SubElement(tbl, f"{{{W_NS}}}tblPr")
    tblStyle = ET.SubElement(tblPr, f"{{{W_NS}}}tblStyle")
    tblStyle.set(f"{{{W_NS}}}val", "TableGrid")
    tblW = ET.SubElement(tblPr, f"{{{W_NS}}}tblW")
    tblW.set(f"{{{W_NS}}}w", "8500")
    tblW.set(f"{{{W_NS}}}type", "dxa")
    jc = ET.SubElement(tblPr, f"{{{W_NS}}}jc")
    jc.set(f"{{{W_NS}}}val", "center")
    
    tblBorders = ET.SubElement(tblPr, f"{{{W_NS}}}tblBorders")
    for b_name in ["top", "left", "bottom", "right", "insideH", "insideV"]:
        b = ET.SubElement(tblBorders, f"{{{W_NS}}}{b_name}")
        b.set(f"{{{W_NS}}}val", "single")
        b.set(f"{{{W_NS}}}sz", "4")
        b.set(f"{{{W_NS}}}space", "0")
        b.set(f"{{{W_NS}}}color", "CBD5E1")
    
    tblLook = ET.SubElement(tblPr, f"{{{W_NS}}}tblLook")
    tblLook.set(f"{{{W_NS}}}val", "04A0")
    tblLook.set(f"{{{W_NS}}}firstRow", "1")
    tblLook.set(f"{{{W_NS}}}noHBand", "0")
    tblLook.set(f"{{{W_NS}}}noVBand", "1")
    
    num_cols = len(headers)
    if not widths:
        w_each = str(8500 // num_cols)
        widths = [w_each] * num_cols
        
    tblGrid = ET.SubElement(tbl, f"{{{W_NS}}}tblGrid")
    for w in widths:
        col = ET.SubElement(tblGrid, f"{{{W_NS}}}gridCol")
        col.set(f"{{{W_NS}}}w", str(w))
        
    # Header Row
    tr_h = ET.SubElement(tbl, f"{{{W_NS}}}tr")
    trPr_h = ET.SubElement(tr_h, f"{{{W_NS}}}trPr")
    tblHeader = ET.SubElement(trPr_h, f"{{{W_NS}}}tblHeader")
    cantSplit = ET.SubElement(trPr_h, f"{{{W_NS}}}cantSplit")
    
    for idx, h_text in enumerate(headers):
        tc = ET.SubElement(tr_h, f"{{{W_NS}}}tc")
        tcPr = ET.SubElement(tc, f"{{{W_NS}}}tcPr")
        tcW = ET.SubElement(tcPr, f"{{{W_NS}}}tcW")
        tcW.set(f"{{{W_NS}}}w", str(widths[idx]))
        tcW.set(f"{{{W_NS}}}type", "dxa")
        shd = ET.SubElement(tcPr, f"{{{W_NS}}}shd")
        shd.set(f"{{{W_NS}}}val", "clear")
        shd.set(f"{{{W_NS}}}color", "auto")
        shd.set(f"{{{W_NS}}}fill", "E2E8F0")
        vAlign = ET.SubElement(tcPr, f"{{{W_NS}}}vAlign")
        vAlign.set(f"{{{W_NS}}}val", "center")
        
        tcMar = ET.SubElement(tcPr, f"{{{W_NS}}}tcMar")
        for m, val in [("top", "80"), ("bottom", "80"), ("left", "100"), ("right", "100")]:
            node = ET.SubElement(tcMar, f"{{{W_NS}}}{m}")
            node.set(f"{{{W_NS}}}w", val)
            node.set(f"{{{W_NS}}}type", "dxa")
            
        p = ET.SubElement(tc, f"{{{W_NS}}}p")
        pPr = ET.SubElement(p, f"{{{W_NS}}}pPr")
        p_jc = ET.SubElement(pPr, f"{{{W_NS}}}jc")
        p_jc.set(f"{{{W_NS}}}val", "center")
        p_sp = ET.SubElement(pPr, f"{{{W_NS}}}spacing")
        p_sp.set(f"{{{W_NS}}}line", "240")
        p_sp.set(f"{{{W_NS}}}before", "40")
        p_sp.set(f"{{{W_NS}}}after", "40")
        
        r = ET.SubElement(p, f"{{{W_NS}}}r")
        rPr = ET.SubElement(r, f"{{{W_NS}}}rPr")
        b = ET.SubElement(rPr, f"{{{W_NS}}}b")
        sz = ET.SubElement(rPr, f"{{{W_NS}}}sz")
        sz.set(f"{{{W_NS}}}val", "20")  # 10pt
        rFonts = ET.SubElement(rPr, f"{{{W_NS}}}rFonts")
        rFonts.set(f"{{{W_NS}}}ascii", "Times New Roman")
        rFonts.set(f"{{{W_NS}}}hAnsi", "Times New Roman")
        t = ET.SubElement(r, f"{{{W_NS}}}t")
        t.set(f"{{{XML_NS}}}space", "preserve")
        t.text = h_text
        
    # Data Rows
    for row in rows:
        tr = ET.SubElement(tbl, f"{{{W_NS}}}tr")
        trPr = ET.SubElement(tr, f"{{{W_NS}}}trPr")
        cantSplit = ET.SubElement(trPr, f"{{{W_NS}}}cantSplit")
        for idx, cell_text in enumerate(row):
            tc = ET.SubElement(tr, f"{{{W_NS}}}tc")
            tcPr = ET.SubElement(tc, f"{{{W_NS}}}tcPr")
            tcW = ET.SubElement(tcPr, f"{{{W_NS}}}tcW")
            tcW.set(f"{{{W_NS}}}w", str(widths[idx]))
            tcW.set(f"{{{W_NS}}}type", "dxa")
            vAlign = ET.SubElement(tcPr, f"{{{W_NS}}}vAlign")
            vAlign.set(f"{{{W_NS}}}val", "center")
            
            tcMar = ET.SubElement(tcPr, f"{{{W_NS}}}tcMar")
            for m, val in [("top", "60"), ("bottom", "60"), ("left", "100"), ("right", "100")]:
                node = ET.SubElement(tcMar, f"{{{W_NS}}}{m}")
                node.set(f"{{{W_NS}}}w", val)
                node.set(f"{{{W_NS}}}type", "dxa")
                
            p = ET.SubElement(tc, f"{{{W_NS}}}p")
            pPr = ET.SubElement(p, f"{{{W_NS}}}pPr")
            p_jc = ET.SubElement(pPr, f"{{{W_NS}}}jc")
            if idx in (0, 1) and len(str(cell_text)) < 25:
                p_jc.set(f"{{{W_NS}}}val", "center")
            elif idx in (2, 3) and len(str(cell_text)) < 15:
                p_jc.set(f"{{{W_NS}}}val", "center")
            else:
                p_jc.set(f"{{{W_NS}}}val", "left")
                
            p_sp = ET.SubElement(pPr, f"{{{W_NS}}}spacing")
            p_sp.set(f"{{{W_NS}}}line", "240")
            p_sp.set(f"{{{W_NS}}}before", "30")
            p_sp.set(f"{{{W_NS}}}after", "30")
            
            r = ET.SubElement(p, f"{{{W_NS}}}r")
            rPr = ET.SubElement(r, f"{{{W_NS}}}rPr")
            sz = ET.SubElement(rPr, f"{{{W_NS}}}sz")
            sz.set(f"{{{W_NS}}}val", "19")  # 9.5pt
            rFonts = ET.SubElement(rPr, f"{{{W_NS}}}rFonts")
            rFonts.set(f"{{{W_NS}}}ascii", "Times New Roman")
            rFonts.set(f"{{{W_NS}}}hAnsi", "Times New Roman")
            t = ET.SubElement(r, f"{{{W_NS}}}t")
            t.set(f"{{{XML_NS}}}space", "preserve")
            t.text = str(cell_text)
            
    return tbl

print("Loaded module dependencies successfully.")
