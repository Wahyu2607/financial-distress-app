import zipfile
import xml.etree.ElementTree as ET
import os

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M_NS = "http://schemas.microsoft.com/office/word/2010/wordml"
ET.register_namespace('w', W_NS)
ET.register_namespace('w14', M_NS)

def make_p(text, style="paragraf", bold=False, jc=None, before=None, after=None, italic=False, sz=None, num_id=None, ilvl=None):
    p = ET.Element(f"{{{W_NS}}}p")
    pPr = ET.SubElement(p, f"{{{W_NS}}}pPr")
    if style:
        pStyle = ET.SubElement(pPr, f"{{{W_NS}}}pStyle")
        pStyle.set(f"{{{W_NS}}}val", style)
    if num_id is not None:
        numPr = ET.SubElement(pPr, f"{{{W_NS}}}numPr")
        ilvl_el = ET.SubElement(numPr, f"{{{W_NS}}}ilvl")
        ilvl_el.set(f"{{{W_NS}}}val", str(ilvl if ilvl is not None else 0))
        numId_el = ET.SubElement(numPr, f"{{{W_NS}}}numId")
        numId_el.set(f"{{{W_NS}}}val", str(num_id))
    if jc:
        jc_el = ET.SubElement(pPr, f"{{{W_NS}}}jc")
        jc_el.set(f"{{{W_NS}}}val", jc)
    if before is not None or after is not None:
        spacing = ET.SubElement(pPr, f"{{{W_NS}}}spacing")
        if before is not None:
            spacing.set(f"{{{W_NS}}}before", str(before))
        if after is not None:
            spacing.set(f"{{{W_NS}}}after", str(after))
    
    r = ET.SubElement(p, f"{{{W_NS}}}r")
    rPr = ET.SubElement(r, f"{{{W_NS}}}rPr")
    if bold:
        ET.SubElement(rPr, f"{{{W_NS}}}b")
    if italic:
        ET.SubElement(rPr, f"{{{W_NS}}}i")
    if sz:
        sz_el = ET.SubElement(rPr, f"{{{W_NS}}}sz")
        sz_el.set(f"{{{W_NS}}}val", str(sz))
    
    t = ET.SubElement(r, f"{{{W_NS}}}t")
    t.text = text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return p

def make_caption(text):
    return make_p(text, style="Caption", bold=True, jc="center", before=120, after=60, sz=22)

def make_heading(text, num_id=17):
    p = ET.Element(f"{{{W_NS}}}p")
    pPr = ET.SubElement(p, f"{{{W_NS}}}pPr")
    pStyle = ET.SubElement(pPr, f"{{{W_NS}}}pStyle")
    pStyle.set(f"{{{W_NS}}}val", "heading30")
    if num_id is not None:
        numPr = ET.SubElement(pPr, f"{{{W_NS}}}numPr")
        ilvl_el = ET.SubElement(numPr, f"{{{W_NS}}}ilvl")
        ilvl_el.set(f"{{{W_NS}}}val", "0")
        numId_el = ET.SubElement(numPr, f"{{{W_NS}}}numId")
        numId_el.set(f"{{{W_NS}}}val", str(num_id))
    spacing = ET.SubElement(pPr, f"{{{W_NS}}}spacing")
    spacing.set(f"{{{W_NS}}}before", "120")
    spacing.set(f"{{{W_NS}}}after", "60")
    ind = ET.SubElement(pPr, f"{{{W_NS}}}ind")
    ind.set(f"{{{W_NS}}}left", "567")
    ind.set(f"{{{W_NS}}}hanging", "567")
    r = ET.SubElement(p, f"{{{W_NS}}}r")
    rPr = ET.SubElement(r, f"{{{W_NS}}}rPr")
    ET.SubElement(rPr, f"{{{W_NS}}}b")
    t = ET.SubElement(r, f"{{{W_NS}}}t")
    t.text = text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return p

def build_table(headers, rows, col_widths, total_w=8500):
    tbl = ET.Element(f"{{{W_NS}}}tbl")
    tblPr = ET.SubElement(tbl, f"{{{W_NS}}}tblPr")
    tblStyle = ET.SubElement(tblPr, f"{{{W_NS}}}tblStyle")
    tblStyle.set(f"{{{W_NS}}}val", "TableGrid")
    tblW = ET.SubElement(tblPr, f"{{{W_NS}}}tblW")
    tblW.set(f"{{{W_NS}}}w", str(total_w))
    tblW.set(f"{{{W_NS}}}type", "dxa")
    jc = ET.SubElement(tblPr, f"{{{W_NS}}}jc")
    jc.set(f"{{{W_NS}}}val", "center")
    tblLook = ET.SubElement(tblPr, f"{{{W_NS}}}tblLook")
    tblLook.set(f"{{{W_NS}}}val", "05E0")
    tblLook.set(f"{{{W_NS}}}firstRow", "1")
    tblLook.set(f"{{{W_NS}}}lastRow", "1")
    
    tblGrid = ET.SubElement(tbl, f"{{{W_NS}}}tblGrid")
    for w in col_widths:
        col = ET.SubElement(tblGrid, f"{{{W_NS}}}gridCol")
        col.set(f"{{{W_NS}}}w", str(w))
    
    # Header row
    tr_h = ET.SubElement(tbl, f"{{{W_NS}}}tr")
    trPr_h = ET.SubElement(tr_h, f"{{{W_NS}}}trPr")
    ET.SubElement(trPr_h, f"{{{W_NS}}}cantSplit")
    ET.SubElement(trPr_h, f"{{{W_NS}}}tblHeader")
    jc_h = ET.SubElement(trPr_h, f"{{{W_NS}}}jc")
    jc_h.set(f"{{{W_NS}}}val", "center")
    
    for idx, (h_text, w) in enumerate(zip(headers, col_widths)):
        tc = ET.SubElement(tr_h, f"{{{W_NS}}}tc")
        tcPr = ET.SubElement(tc, f"{{{W_NS}}}tcPr")
        tcW = ET.SubElement(tcPr, f"{{{W_NS}}}tcW")
        tcW.set(f"{{{W_NS}}}w", str(w))
        tcW.set(f"{{{W_NS}}}type", "dxa")
        shd = ET.SubElement(tcPr, f"{{{W_NS}}}shd")
        shd.set(f"{{{W_NS}}}val", "clear")
        shd.set(f"{{{W_NS}}}color", "auto")
        shd.set(f"{{{W_NS}}}fill", "E2E8F0")
        tcMar = ET.SubElement(tcPr, f"{{{W_NS}}}tcMar")
        for m in ['top', 'bottom']:
            el = ET.SubElement(tcMar, f"{{{W_NS}}}{m}")
            el.set(f"{{{W_NS}}}w", "80")
            el.set(f"{{{W_NS}}}type", "dxa")
        for m in ['left', 'right']:
            el = ET.SubElement(tcMar, f"{{{W_NS}}}{m}")
            el.set(f"{{{W_NS}}}w", "100")
            el.set(f"{{{W_NS}}}type", "dxa")
        vAlign = ET.SubElement(tcPr, f"{{{W_NS}}}vAlign")
        vAlign.set(f"{{{W_NS}}}val", "center")
        
        p = ET.SubElement(tc, f"{{{W_NS}}}p")
        pPr = ET.SubElement(p, f"{{{W_NS}}}pPr")
        spacing = ET.SubElement(pPr, f"{{{W_NS}}}spacing")
        spacing.set(f"{{{W_NS}}}before", "40")
        spacing.set(f"{{{W_NS}}}after", "40")
        p_jc = ET.SubElement(pPr, f"{{{W_NS}}}jc")
        p_jc.set(f"{{{W_NS}}}val", "center")
        r = ET.SubElement(p, f"{{{W_NS}}}r")
        rPr = ET.SubElement(r, f"{{{W_NS}}}rPr")
        ET.SubElement(rPr, f"{{{W_NS}}}b")
        sz = ET.SubElement(rPr, f"{{{W_NS}}}sz")
        sz.set(f"{{{W_NS}}}val", "20")
        t = ET.SubElement(r, f"{{{W_NS}}}t")
        t.text = h_text
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    
    # Data rows
    for row_info in rows:
        # row_info can be (cells, is_subtotal, aligns)
        cells = row_info['cells']
        is_subtotal = row_info.get('is_subtotal', False)
        aligns = row_info.get('aligns', ['center'] * len(cells))
        bg_fill = row_info.get('bg_fill', "F8FAFC" if is_subtotal else None)
        bold = row_info.get('bold', is_subtotal)
        
        tr = ET.SubElement(tbl, f"{{{W_NS}}}tr")
        trPr = ET.SubElement(tr, f"{{{W_NS}}}trPr")
        ET.SubElement(trPr, f"{{{W_NS}}}cantSplit")
        tr_jc = ET.SubElement(trPr, f"{{{W_NS}}}jc")
        tr_jc.set(f"{{{W_NS}}}val", "center")
        
        for c_text, w, alg in zip(cells, col_widths, aligns):
            tc = ET.SubElement(tr, f"{{{W_NS}}}tc")
            tcPr = ET.SubElement(tc, f"{{{W_NS}}}tcPr")
            tcW = ET.SubElement(tcPr, f"{{{W_NS}}}tcW")
            tcW.set(f"{{{W_NS}}}w", str(w))
            tcW.set(f"{{{W_NS}}}type", "dxa")
            if bg_fill:
                shd = ET.SubElement(tcPr, f"{{{W_NS}}}shd")
                shd.set(f"{{{W_NS}}}val", "clear")
                shd.set(f"{{{W_NS}}}color", "auto")
                shd.set(f"{{{W_NS}}}fill", bg_fill)
            tcMar = ET.SubElement(tcPr, f"{{{W_NS}}}tcMar")
            for m in ['top', 'bottom']:
                el = ET.SubElement(tcMar, f"{{{W_NS}}}{m}")
                el.set(f"{{{W_NS}}}w", "60")
                el.set(f"{{{W_NS}}}type", "dxa")
            for m in ['left', 'right']:
                el = ET.SubElement(tcMar, f"{{{W_NS}}}{m}")
                el.set(f"{{{W_NS}}}w", "100")
                el.set(f"{{{W_NS}}}type", "dxa")
            vAlign = ET.SubElement(tcPr, f"{{{W_NS}}}vAlign")
            vAlign.set(f"{{{W_NS}}}val", "center")
            
            p = ET.SubElement(tc, f"{{{W_NS}}}p")
            pPr = ET.SubElement(p, f"{{{W_NS}}}pPr")
            spacing = ET.SubElement(pPr, f"{{{W_NS}}}spacing")
            spacing.set(f"{{{W_NS}}}before", "30")
            spacing.set(f"{{{W_NS}}}after", "30")
            p_jc = ET.SubElement(pPr, f"{{{W_NS}}}jc")
            p_jc.set(f"{{{W_NS}}}val", alg)
            
            r = ET.SubElement(p, f"{{{W_NS}}}r")
            rPr = ET.SubElement(r, f"{{{W_NS}}}rPr")
            if bold:
                ET.SubElement(rPr, f"{{{W_NS}}}b")
            sz = ET.SubElement(rPr, f"{{{W_NS}}}sz")
            sz.set(f"{{{W_NS}}}val", "19")
            t = ET.SubElement(r, f"{{{W_NS}}}t")
            t.text = str(c_text)
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            
    return tbl

print("build_table defined successfully.")
