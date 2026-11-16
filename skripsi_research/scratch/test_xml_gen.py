import xml.etree.ElementTree as ET

# Test creating paragraph with Arial formatting
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"

def make_r(text, bold=False, size=None, color=None):
    r = ET.Element(f"{{{A_NS}}}r")
    rPr = ET.SubElement(r, f"{{{A_NS}}}rPr", lang="en-US", dirty="0")
    if bold:
        rPr.set("b", "1")
    if size:
        rPr.set("sz", str(size))
    
    solidFill = ET.SubElement(rPr, f"{{{A_NS}}}solidFill")
    if color:
        ET.SubElement(solidFill, f"{{{A_NS}}}srgbClr", val=color)
    else:
        ET.SubElement(solidFill, f"{{{A_NS}}}schemeClr", val="bg1")
        
    ET.SubElement(rPr, f"{{{A_NS}}}latin", typeface="Arial")
    ET.SubElement(rPr, f"{{{A_NS}}}cs", typeface="Arial")
    
    t = ET.SubElement(r, f"{{{A_NS}}}t")
    t.text = text
    return r

p = ET.Element(f"{{{A_NS}}}p")
p.append(make_r("Test Arial", bold=True, size=1600))
print(ET.tostring(p, encoding="utf-8").decode("utf-8"))
