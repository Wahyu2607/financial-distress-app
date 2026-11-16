import re
import numpy as np
import pandas as pd

# 1. parse_financial_number
def parse_financial_number(value):
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    text = text.replace(' ', '').replace('Rp', '').replace('IDR', '').replace('$', '')
    if text.lower() in ('-', 'nihil', 'nil', 'null', 'none', ''):
        return 0.0

    is_parenthesized = False
    clean_paren = re.sub(r'\s+', '', text)
    if clean_paren.startswith('(') and clean_paren.endswith(')'):
        is_parenthesized = True
        text = clean_paren[1:-1]

    text = re.sub(r'[^\d,.\-]', '', text)
    if not text or text == '-':
        return 0.0 if text == '-' else None

    if ',' in text and '.' in text:
        if text.rfind(',') > text.rfind('.'):
            text = text.replace('.', '').replace(',', '.')
        else:
            text = text.replace(',', '')
    elif ',' in text:
        if re.search(r',\d{1,2}$', text):
            text = text.replace(',', '.')
        else:
            text = text.replace(',', '')
    elif '.' in text:
        # Check if dot is thousands separator (e.g. 4.520.350.000 or 8.950.000)
        if text.count('.') > 1 or re.search(r'\.\d{3}$', text):
            text = text.replace('.', '')

    try:
        val = float(text)
        return -val if is_parenthesized else val
    except ValueError:
        return None

# 2. complete_financial_values
def complete_financial_values(fin: dict) -> dict:
    completed = dict(fin)
    
    # 1. Beban Bunga
    completed['interest_expense'] = abs(float(completed.get('interest_expense', 0.0) or 0.0))
    
    # 2. EBIT jika kosong tapi PBT dan Bunga ada
    if not completed.get('ebit') and completed.get('pbt'):
        completed['ebit'] = float(completed['pbt']) + completed['interest_expense']
    elif not completed.get('ebit') and completed.get('operating_income'):
        completed['ebit'] = float(completed['operating_income'])
    elif not completed.get('ebit') and completed.get('net_income'):
        completed['ebit'] = float(completed['net_income']) + completed['interest_expense']
        
    # 3. Penutupan Neraca
    ta = completed.get('total_assets')
    tl = completed.get('total_liabilities')
    eq = completed.get('total_equity')
    ca = completed.get('current_assets')
    cl = completed.get('current_liabilities')
    
    if ta and tl and not eq:
        completed['total_equity'] = float(ta) - float(tl)
    elif ta and eq and not tl:
        completed['total_liabilities'] = float(ta) - float(eq)
    elif tl and eq and not ta:
        completed['total_assets'] = float(tl) + float(eq)
        
    # 4. Modal Kerja Bersih
    if ca is not None and cl is not None and not completed.get('working_capital'):
        completed['working_capital'] = float(ca) - float(cl)
        
    # 5. Rekonsiliasi Ekuitas Modal Sendiri
    if not completed.get('common_stock_equity') and completed.get('total_equity'):
        completed['common_stock_equity'] = float(completed['total_equity'])
        
    return completed

# 3. build_features_from_financials
def build_features_from_financials(fin: dict, cap_ratios: bool = True) -> dict:
    ta = float(fin.get('total_assets', 0.0) or 0.0)
    tl = float(fin.get('total_liabilities', 0.0) or 0.0)
    ca = float(fin.get('current_assets', 0.0) or 0.0)
    cl = float(fin.get('current_liabilities', 0.0) or 0.0)
    wc = float(fin.get('working_capital', ca - cl))
    re = float(fin.get('retained_earnings', 0.0) or 0.0)
    ebit = float(fin.get('ebit', 0.0) or 0.0)
    eq = float(fin.get('common_stock_equity', fin.get('total_equity', 0.0)) or 0.0)
    rev = float(fin.get('revenue', fin.get('total_revenue', 0.0)) or 0.0)
    
    safe_ta = ta if abs(ta) > 1e-5 else 1.0
    safe_tl = tl if abs(tl) > 1e-5 else 1.0
    
    raw_ratios = {
        'X1': wc / safe_ta,
        'X2': re / safe_ta,
        'X3': ebit / safe_ta,
        'X4': eq / safe_tl,
        'X5': rev / safe_ta
    }
    return raw_ratios

# 4. clean_and_cap_ratios
def clean_and_cap_ratios(ratios: dict, cap_x4_max: float = 3.0, cap_outliers: bool = True) -> tuple[dict, dict]:
    clean = dict(ratios)
    audit = {}
    
    # X1: [-2.0, 2.0]
    r_x1 = clean.get('X1', 0.0)
    c_x1 = np.clip(r_x1, -2.0, 2.0) if cap_outliers else r_x1
    clean['X1'] = float(c_x1)
    audit['X1'] = {'raw': r_x1, 'clean': c_x1, 'capped': r_x1 != c_x1}
    
    # X2: [-5.0, 3.0]
    r_x2 = clean.get('X2', 0.0)
    c_x2 = np.clip(r_x2, -5.0, 3.0) if cap_outliers else r_x2
    clean['X2'] = float(c_x2)
    audit['X2'] = {'raw': r_x2, 'clean': c_x2, 'capped': r_x2 != c_x2}
    
    # X3: [-2.0, 2.0]
    r_x3 = clean.get('X3', 0.0)
    c_x3 = np.clip(r_x3, -2.0, 2.0) if cap_outliers else r_x3
    clean['X3'] = float(c_x3)
    audit['X3'] = {'raw': r_x3, 'clean': c_x3, 'capped': r_x3 != c_x3}
    
    # X4: [0.0, cap_x4_max]
    r_x4 = clean.get('X4', 0.0)
    c_x4 = np.clip(r_x4, 0.0, cap_x4_max)
    clean['X4'] = float(c_x4)
    audit['X4'] = {'raw': r_x4, 'clean': c_x4, 'capped': r_x4 != c_x4}
    
    return clean, audit

print("All preprocessing functions compiled successfully.")
