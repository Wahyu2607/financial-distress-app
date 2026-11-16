import os
import shutil
import zipfile
import xml.etree.ElementTree as ET

# Namespaces
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
P14_NS = "http://schemas.microsoft.com/office/powerpoint/2010/main"
A14_NS = "http://schemas.microsoft.com/office/drawing/2010/main"
A16_NS = "http://schemas.microsoft.com/office/drawing/2014/main"

for prefix, uri in [
    ('p', P_NS), ('a', A_NS), ('r', R_NS), ('m', M_NS),
    ('mc', MC_NS), ('p14', P14_NS), ('a14', A14_NS), ('a16', A16_NS)
]:
    ET.register_namespace(prefix, uri)

def make_r(text, bold=False, italic=False, size=None, color=None, scheme=None):
    r = ET.Element(f"{{{A_NS}}}r")
    rPr = ET.SubElement(r, f"{{{A_NS}}}rPr", lang="en-US", dirty="0")
    if bold:
        rPr.set("b", "1")
    if italic:
        rPr.set("i", "1")
    if size:
        rPr.set("sz", str(size))
    
    solidFill = ET.SubElement(rPr, f"{{{A_NS}}}solidFill")
    if color:
        ET.SubElement(solidFill, f"{{{A_NS}}}srgbClr", val=color)
    elif scheme:
        ET.SubElement(solidFill, f"{{{A_NS}}}schemeClr", val=scheme)
    else:
        ET.SubElement(solidFill, f"{{{A_NS}}}schemeClr", val="bg1")
        
    ET.SubElement(rPr, f"{{{A_NS}}}latin", typeface="Arial")
    ET.SubElement(rPr, f"{{{A_NS}}}cs", typeface="Arial")
    
    t = ET.SubElement(r, f"{{{A_NS}}}t")
    t.text = text
    return r

def make_p(runs, align="l", space_after=600, line_spacing=120000):
    p = ET.Element(f"{{{A_NS}}}p")
    pPr = ET.SubElement(p, f"{{{A_NS}}}pPr", algn=align)
    if space_after:
        spcAft = ET.SubElement(pPr, f"{{{A_NS}}}spcAft")
        ET.SubElement(spcAft, f"{{{A_NS}}}spcPts", val=str(space_after))
    if line_spacing:
        lnSpc = ET.SubElement(pPr, f"{{{A_NS}}}lnSpc")
        ET.SubElement(lnSpc, f"{{{A_NS}}}spcPct", val=str(line_spacing))
        
    for r in runs:
        if isinstance(r, tuple):
            text = r[0]
            bold = r[1] if len(r) > 1 else False
            size = r[2] if len(r) > 2 else None
            color = r[3] if len(r) > 3 else None
            scheme = r[4] if len(r) > 4 else None
            p.append(make_r(text, bold=bold, size=size, color=color, scheme=scheme))
        else:
            p.append(r)
            
    endParaRPr = ET.SubElement(p, f"{{{A_NS}}}endParaRPr", lang="en-ID", dirty="0")
    ET.SubElement(endParaRPr, f"{{{A_NS}}}latin", typeface="Arial")
    ET.SubElement(endParaRPr, f"{{{A_NS}}}cs", typeface="Arial")
    fill = ET.SubElement(endParaRPr, f"{{{A_NS}}}solidFill")
    ET.SubElement(fill, f"{{{A_NS}}}schemeClr", val="bg1")
    return p

def set_shape_text(sp, paragraphs_runs, align="l"):
    txBody = sp.find(f"{{{P_NS}}}txBody")
    if txBody is None:
        txBody = ET.SubElement(sp, f"{{{P_NS}}}txBody")
        ET.SubElement(txBody, f"{{{A_NS}}}bodyPr")
        ET.SubElement(txBody, f"{{{A_NS}}}lstStyle")
    else:
        for p in list(txBody.findall(f"{{{A_NS}}}p")):
            txBody.remove(p)
            
    for p_runs in paragraphs_runs:
        txBody.append(make_p(p_runs, align=align))

def create_textbox_shape(shape_id, shape_name, x, y, cx, cy, paragraphs_runs, bg_color=None, border_color=None, align="l"):
    sp = ET.Element(f"{{{P_NS}}}sp")
    nvSpPr = ET.SubElement(sp, f"{{{P_NS}}}nvSpPr")
    ET.SubElement(nvSpPr, f"{{{P_NS}}}cNvPr", id=str(shape_id), name=shape_name)
    ET.SubElement(nvSpPr, f"{{{P_NS}}}cNvSpPr", txBox="1")
    ET.SubElement(nvSpPr, f"{{{P_NS}}}nvPr")
    
    spPr = ET.SubElement(sp, f"{{{P_NS}}}spPr")
    xfrm = ET.SubElement(spPr, f"{{{A_NS}}}xfrm")
    ET.SubElement(xfrm, f"{{{A_NS}}}off", x=str(x), y=str(y))
    ET.SubElement(xfrm, f"{{{A_NS}}}ext", cx=str(cx), cy=str(cy))
    
    prstGeom = ET.SubElement(spPr, f"{{{A_NS}}}prstGeom", prst="roundRect" if bg_color else "rect")
    ET.SubElement(prstGeom, f"{{{A_NS}}}avLst")
    if bg_color:
        solidFill = ET.SubElement(spPr, f"{{{A_NS}}}solidFill")
        ET.SubElement(solidFill, f"{{{A_NS}}}srgbClr", val=bg_color)
    else:
        ET.SubElement(spPr, f"{{{A_NS}}}noFill")
        
    if border_color:
        ln = ET.SubElement(spPr, f"{{{A_NS}}}ln", w="19050")
        lnFill = ET.SubElement(ln, f"{{{A_NS}}}solidFill")
        ET.SubElement(lnFill, f"{{{A_NS}}}srgbClr", val=border_color)
    
    txBody = ET.SubElement(sp, f"{{{P_NS}}}txBody")
    bodyPr = ET.SubElement(txBody, f"{{{A_NS}}}bodyPr", wrap="square", rtlCol="0")
    if bg_color:
        bodyPr.set("lIns", "182880")
        bodyPr.set("tIns", "146304")
        bodyPr.set("rIns", "182880")
        bodyPr.set("bIns", "146304")
    ET.SubElement(txBody, f"{{{A_NS}}}lstStyle")
    
    for p_runs in paragraphs_runs:
        txBody.append(make_p(p_runs, align=align))
        
    return sp

print("Setup completed successfully.")
