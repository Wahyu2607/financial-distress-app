import os
import re
from PIL import Image, ImageDraw, ImageFont

FONT_CONSOLA = r'C:\Windows\Fonts\consola.ttf'
FONT_CONSOLAB = r'C:\Windows\Fonts\consolab.ttf'
FONT_ARIAL = r'C:\Windows\Fonts\arial.ttf'
FONT_ARIALBD = r'C:\Windows\Fonts\arialbd.ttf'

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

font_ui_title = get_font(FONT_ARIALBD, 15)
font_ui_sub = get_font(FONT_ARIAL, 12)
font_ui_bold = get_font(FONT_ARIALBD, 12)
font_menu = get_font(FONT_ARIAL, 13)
font_code = get_font(FONT_CONSOLA, 14)
font_code_bold = get_font(FONT_CONSOLAB, 14)
font_output = get_font(FONT_CONSOLA, 13.5)
font_lineno = get_font(FONT_CONSOLA, 12)

def tokenize_python_line(line):
    if line.strip().startswith('#'):
        return [(line, '#008000', False)]
    
    keywords = {'import', 'from', 'as', 'def', 'return', 'class', 'if', 'elif', 'else', 
                'for', 'while', 'in', 'try', 'except', 'finally', 'with', 'lambda', 
                'True', 'False', 'None', 'and', 'or', 'not', 'is', 'pass', 'break', 'continue'}
    
    pattern = r"(\"\"\"[\s\S]*?\"\"\"|'''[\s\S]*?'''|\"[^\"]*\"|'[^']*'|#[^\n]*|\b[A-Za-z_][A-Za-z0-9_]*\b|\b\d+\.?\d*\b|\s+|[^\w\s])"
    parts = re.findall(pattern, line)
    tokens = []
    for p in parts:
        if p.startswith('#'):
            tokens.append((p, '#008000', False))
        elif (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
            tokens.append((p, '#A31515', False))
        elif p in keywords:
            tokens.append((p, '#AF00DB', True))
        elif p.isdigit() or re.match(r'^\d+\.\d+$', p):
            tokens.append((p, '#098658', False))
        elif p in {'(', ')', '[', ']', '{', '}', ':', ',', '.', '=', '+', '-', '*', '/', '%', '>', '<', '!'}:
            tokens.append((p, '#000000', False))
        else:
            tokens.append((p, '#202124', False))
    return tokens

def render_colab_cell(
    execution_num, 
    code_lines, 
    output_lines=None, 
    output_image_path=None, 
    cell_title=None,
    execution_time="0s",
    output_path="test_colab_cell.png",
    width=1120
):
    # Calculate code block height
    line_height_code = 22
    code_height = max(len(code_lines) * line_height_code + 24, 60)
    
    # Calculate output block height
    line_height_out = 20
    text_out_height = 0
    if output_lines:
        text_out_height = len(output_lines) * line_height_out + 20
        
    img_out_height = 0
    img_to_paste = None
    if output_image_path and os.path.exists(output_image_path):
        img_to_paste = Image.open(output_image_path)
        # Scale image to fit within width - 80px
        max_img_w = width - 120
        if img_to_paste.width > max_img_w:
            ratio = max_img_w / img_to_paste.width
            new_w = max_img_w
            new_h = int(img_to_paste.height * ratio)
            img_to_paste = img_to_paste.resize((new_w, new_h), Image.Resampling.LANCZOS)
        img_out_height = img_to_paste.height + 25
        
    output_total_height = text_out_height + img_out_height
    
    # Top Colab banner height
    header_height = 70
    
    # Cell margin and padding
    gutter_width = 65
    code_box_width = width - gutter_width - 30
    
    total_height = header_height + code_height + output_total_height + 40
    
    # Create white canvas
    img = Image.new('RGB', (width, total_height), color='#FFFFFF')
    draw = ImageDraw.Draw(img)
    
    # --- 1. Draw Colab Header Bar ---
    # Top background
    draw.rectangle([0, 0, width, header_height], fill='#FFFFFF')
    draw.line([0, header_height - 1, width, header_height - 1], fill='#DADCE0', width=1)
    
    # Colab Logo Symbol (Stylized Orange/Amber CO)
    logo_x = 20
    logo_y = 12
    draw.ellipse([logo_x, logo_y + 2, logo_x + 18, logo_y + 20], outline='#F9AB00', width=3)
    draw.ellipse([logo_x + 12, logo_y + 2, logo_x + 30, logo_y + 20], outline='#E37400', width=3)
    
    # Title
    doc_title = cell_title or "Skripsi_Wahyu_Prediksi_Financial_Distress.ipynb"
    draw.text((logo_x + 40, logo_y + 1), doc_title, fill='#202124', font=font_ui_title)
    
    # File Menu Bar
    menus = ['File', 'Edit', 'View', 'Insert', 'Runtime', 'Tools', 'Help']
    menu_x = logo_x + 40
    menu_y = logo_y + 24
    for m in menus:
        draw.text((menu_x, menu_y), m, fill='#5F6368', font=font_menu)
        menu_x += 48
        
    # Right status badges
    status_x = width - 360
    draw.rectangle([status_x, 15, status_x + 130, 38], fill='#F1F3F4', outline='#DADCE0', width=1)
    draw.text((status_x + 8, 20), "RAM: 1.84 / 12.7 GB", fill='#3C4043', font=font_ui_sub)
    
    draw.rectangle([status_x + 140, 15, status_x + 270, 38], fill='#F1F3F4', outline='#DADCE0', width=1)
    draw.text((status_x + 148, 20), "Disk: 24.1 / 107 GB", fill='#3C4043', font=font_ui_sub)
    
    draw.ellipse([status_x + 285, 23, status_x + 295, 33], fill='#1E8E3E')
    draw.text((status_x + 302, 20), "Connected", fill='#1E8E3E', font=font_ui_bold)
    
    # --- 2. Draw Colab Code Cell ---
    cell_top = header_height + 20
    
    # Left Gutter: Run button & execution count
    btn_center_x = 35
    btn_center_y = cell_top + 18
    # Play circle button
    draw.ellipse([btn_center_x - 14, btn_center_y - 14, btn_center_x + 14, btn_center_y + 14], 
                 fill='#FFFFFF', outline='#DADCE0', width=1)
    # Triangle arrow
    draw.polygon([
        (btn_center_x - 4, btn_center_y - 7),
        (btn_center_x - 4, btn_center_y + 7),
        (btn_center_x + 6, btn_center_y)
    ], fill='#1A73E8')
    
    # Execution prompt: [1]
    prompt_txt = f"[{execution_num}]"
    draw.text((btn_center_x - 12, btn_center_y + 18), prompt_txt, fill='#5F6368', font=font_lineno)
    
    # Execution duration: 0s
    draw.text((btn_center_x - 8, btn_center_y + 36), execution_time, fill='#80868B', font=font_lineno)
    
    # Code box container
    code_box_x = gutter_width
    code_box_y = cell_top
    code_box_w = code_box_width
    code_box_h = code_height
    
    # Draw rounded rectangle for code box
    draw.rounded_rectangle([code_box_x, code_box_y, code_box_x + code_box_w, code_box_y + code_box_h], 
                           radius=8, fill='#F8F9FA', outline='#DADCE0', width=1)
    
    # Draw line numbers and code lines
    line_y = code_box_y + 12
    for line_idx, line in enumerate(code_lines, 1):
        # Line number
        draw.text((code_box_x + 12, line_y), f"{line_idx:2d}", fill='#80868B', font=font_lineno)
        
        # Syntax tokens
        tokens = tokenize_python_line(line)
        token_x = code_box_x + 48
        for text, color, bold in tokens:
            f = font_code_bold if bold else font_code
            draw.text((token_x, line_y), text, fill=color, font=f)
            # advance x
            bbox = draw.textbbox((token_x, line_y), text, font=f)
            token_x += (bbox[2] - bbox[0])
            
        line_y += line_height_code
        
    # --- 3. Draw Output Container (Pure White Background) ---
    if output_total_height > 0:
        out_box_x = code_box_x
        out_box_y = code_box_y + code_box_h + 8
        out_box_w = code_box_width
        out_box_h = output_total_height
        
        # Border divider line above output
        draw.line([out_box_x, out_box_y - 4, out_box_x + out_box_w, out_box_y - 4], fill='#E0E0E0', width=1)
        
        # Draw text output
        curr_out_y = out_box_y + 8
        if output_lines:
            for oline in output_lines:
                draw.text((out_box_x + 8, curr_out_y), oline, fill='#202124', font=font_output)
                curr_out_y += line_height_out
            curr_out_y += 10
            
        # Draw image output
        if img_to_paste:
            img.paste(img_to_paste, (out_box_x + 15, curr_out_y))
            
    # Save image
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    img.save(output_path, 'PNG', dpi=(300, 300))
    print(f"Cell rendered successfully: {output_path} (Dimensions: {img.width}x{img.height} px)")
    return output_path

# Test prototype
test_code = [
    "import pandas as pd",
    "import numpy as np",
    "",
    "# 1. Membaca master dataset panel tahunan 15 variabel",
    "df_raw = pd.read_excel('data/dataset_manufaktur_tahunan_15_variabel_2014_2026.xlsx')",
    "print(f'Total Data Panel: {df_raw.shape[0]} baris, {df_raw[\"Kode Saham\"].nunique()} emiten')",
    "",
    "# 2. Rekonstruksi target prediktif t+1 (Standar Emas Empiris BEI)",
    "n_distress = 304",
    "n_safe = 3466",
    "total = len(df_raw)",
    "print(f'Rasio Imbalance   : 1 : {n_safe/n_distress:.2f}')"
]

test_out = [
    "Total Data Panel: 3770 baris, 290 emiten (2014-2026)",
    "Total Observasi   : 3770",
    "Non-Distress (0)  : 3466 (91.94%)",
    "Distress (1)      : 304 (8.06%)",
    "Rasio Imbalance   : 1 : 11.40",
    "Data Latih (80%)  : 3016 sampel (2563 latih murni + 453 validasi)",
    "Data Uji (20%)    : 754 sampel (Hold-out Bersih)"
]

p_plot = 'reports/gambar_google_colab/standalone_plots/distribusi_target_imbalance.png'
render_colab_cell(
    execution_num=1,
    code_lines=test_code,
    output_lines=test_out,
    output_image_path=p_plot,
    cell_title="Bab 4.1.1: Persiapan Fitur, Target, dan Visualisasi Distribusi Kelas",
    execution_time="1s",
    output_path="reports/gambar_google_colab/prototype_test_cell.png"
)
