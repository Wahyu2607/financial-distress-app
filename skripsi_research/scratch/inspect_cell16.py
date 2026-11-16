import json

nb = json.load(open('financial_distress_bab3_bab4.ipynb', encoding='utf-8'))
print('--- CELL 16 ---')
print(''.join(nb['cells'][16]['source']))
