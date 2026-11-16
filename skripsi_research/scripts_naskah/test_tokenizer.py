import os
import re
from PIL import Image, ImageDraw, ImageFont

FONT_CONSOLA = r'C:\Windows\Fonts\consola.ttf'
FONT_CONSOLAB = r'C:\Windows\Fonts\consolab.ttf'
FONT_ARIAL = r'C:\Windows\Fonts\arial.ttf'
FONT_ARIALBD = r'C:\Windows\Fonts\arialbd.ttf'

def get_font(font_path, size):
    try:
        return ImageFont.truetype(font_path, size)
    except:
        return ImageFont.load_default()

def tokenize_python_line(line):
    """Simple syntax highlighter for Python code."""
    tokens = []
    # Check if comment
    if line.strip().startswith('#'):
        return [(line, '#008000', False)]  # Green for comments
    
    # Regex pattern for keywords, strings, numbers, operators
    keywords = {'import', 'from', 'as', 'def', 'return', 'class', 'if', 'elif', 'else', 
                'for', 'while', 'in', 'try', 'except', 'finally', 'with', 'lambda', 
                'True', 'False', 'None', 'and', 'or', 'not', 'is', 'pass', 'break', 'continue'}
    
    # Pattern to match strings, words, numbers, symbols, spaces
    pattern = r"(\"\"\"[\s\S]*?\"\"\"|'''[\s\S]*?'''|\"[^\"]*\"|'[^']*'|#[^\n]*|\b[A-Za-z_][A-Za-z0-9_]*\b|\b\d+\.?\d*\b|\s+|[^\w\s])"
    parts = re.findall(pattern, line)
    
    for p in parts:
        if p.startswith('#'):
            tokens.append((p, '#008000', False))
        elif (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
            tokens.append((p, '#A31515', False))  # Red for strings
        elif p in keywords:
            tokens.append((p, '#AF00DB', True))   # Purple bold for keywords
        elif p.isdigit() or re.match(r'^\d+\.\d+$', p):
            tokens.append((p, '#098658', False))  # Green-teal for numbers
        elif p in {'(', ')', '[', ']', '{', '}', ':', ',', '.', '=', '+', '-', '*', '/', '%', '>', '<', '!'}:
            tokens.append((p, '#000000', False))
        else:
            tokens.append((p, '#202124', False))  # Standard text
            
    return tokens

print("Syntax tokenizer initialized.")
