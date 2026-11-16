import json

for name in ['financial_distress_bab3_bab4.ipynb', 'financial_distress_model.ipynb']:
    print(f"=== {name} ===")
    nb = json.load(open(name, encoding='utf-8'))
    for i, c in enumerate(nb['cells']):
        src = ''.join(c.get('source', []))[:100].replace('\n', ' ')
        print(f"Cell {i} ({c.get('cell_type')}): {src}")
