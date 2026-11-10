import xml.etree.ElementTree as ET

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
ET.register_namespace('w', W_NS)

def make_p(text, style="paragraf", bold=False, jc=None, before=None, after=None):
    p = ET.Element(f"{{{W_NS}}}p")
    pPr = ET.SubElement(p, f"{{{W_NS}}}pPr")
    if style:
        pStyle = ET.SubElement(pPr, f"{{{W_NS}}}pStyle")
        pStyle.set(f"{{{W_NS}}}val", style)
    if jc:
        jc_el = ET.SubElement(pPr, f"{{{W_NS}}}jc")
        jc_el.set(f"{{{W_NS}}}val", jc)
    if before or after:
        spacing = ET.SubElement(pPr, f"{{{W_NS}}}spacing")
        if before:
            spacing.set(f"{{{W_NS}}}before", str(before))
        if after:
            spacing.set(f"{{{W_NS}}}after", str(after))
    
    r = ET.SubElement(p, f"{{{W_NS}}}r")
    rPr = ET.SubElement(r, f"{{{W_NS}}}rPr")
    if bold:
        ET.SubElement(rPr, f"{{{W_NS}}}b")
    
    t = ET.SubElement(r, f"{{{W_NS}}}t")
    t.text = text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return p

print("make_p works:", ET.tostring(make_p("Testing")).decode('utf-8')[:100])
