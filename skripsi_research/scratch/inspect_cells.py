import json

nb = json.load(open('financial_distress_bab3_bab4.ipynb', encoding='utf-8'))
for idx in [4, 6, 7, 8, 16, 20, 22, 24]:
    print(f"--- CELL {idx} ---")
    print(''.join(nb['cells'][idx]['source']))
