import openpyxl, re
import numpy as np

wb = openpyxl.load_workbook('Uji Coba (UAT) Sistem Prediksi Financial Distress Manufaktur BEI (Jawaban).xlsx')
sheet = wb.active

headers = [sheet.cell(1, c).value for c in range(1, sheet.max_column + 1)]
n_resp = sheet.max_row - 1
print(f'Total Responden Valid: {n_resp}')

# 1. Demographics
ages = {}
profs = {}
for r in range(2, sheet.max_row + 1):
    a = str(sheet.cell(r, 4).value).strip()
    ages[a] = ages.get(a, 0) + 1
    p = str(sheet.cell(r, 5).value).strip()
    profs[p] = profs.get(p, 0) + 1

print('\n=== DEMOGRAFI USIA ===')
for k, v in sorted(ages.items()):
    print(f'- {k}: {v} orang ({v/n_resp*100:.1f}%)')

print('\n=== DEMOGRAFI PROFESI ===')
grouped_profs = {
    'Akademisi / Dosen / Mahasiswa (Ekonomi / Bisnis / Informatika)': 0,
    'Pengembang / Praktisi IT / Data Scientist': 0,
    'Analis Keuangan / Praktisi Pasar Modal / Akuntan': 0,
    'Praktisi Industri / Karyawan Swasta / Profesional': 0,
    'Lainnya / Umum': 0
}

for p, count in profs.items():
    p_lower = p.lower()
    if 'akademisi' in p_lower or 'dosen' in p_lower or 'mahasiswa' in p_lower:
        grouped_profs['Akademisi / Dosen / Mahasiswa (Ekonomi / Bisnis / Informatika)'] += count
    elif 'pengembang' in p_lower or 'it' in p_lower or 'data scientist' in p_lower:
        grouped_profs['Pengembang / Praktisi IT / Data Scientist'] += count
    elif 'analis' in p_lower or 'pasar modal' in p_lower or 'akuntan' in p_lower:
        grouped_profs['Analis Keuangan / Praktisi Pasar Modal / Akuntan'] += count
    elif 'karyawan' in p_lower or 'pegawai' in p_lower:
        grouped_profs['Praktisi Industri / Karyawan Swasta / Profesional'] += count
    else:
        grouped_profs['Lainnya / Umum'] += count

for k, v in grouped_profs.items():
    print(f'- {k}: {v} orang ({v/n_resp*100:.1f}%)')

print('\n=== ANALISIS BUTIR KUESIONER (19 BUTIR) ===')
q_items = []
for c in range(6, 25):
    header = headers[c-1]
    m = re.search(r'\[(.*?)\]', header)
    q_text = m.group(1) if m else header
    
    dim = 'Dimensi A' if c <= 15 else 'Dimensi B'
    
    scores = []
    freq = {1:0, 2:0, 3:0, 4:0, 5:0}
    for r in range(2, sheet.max_row + 1):
        raw_val = str(sheet.cell(r, c).value)
        match = re.match(r'(\d+)', raw_val)
        val = int(match.group(1)) if match else 0
        scores.append(val)
        if val in freq:
            freq[val] += 1
            
    tot = sum(scores)
    max_tot = n_resp * 5
    pct = (tot / max_tot) * 100
    mean = np.mean(scores)
    std = np.std(scores)
    
    q_items.append({
        'num': c - 5,
        'dim': dim,
        'text': q_text,
        'tot': tot,
        'max': max_tot,
        'mean': mean,
        'std': std,
        'pct': pct,
        'freq': freq
    })

for q in q_items:
    d = q['dim']
    num = q['num']
    t = q['text'][:55]
    tot = q['tot']
    m = q['mean']
    pct = q['pct']
    print(f'Q{num:2d} [{d}]: {t} | Tot={tot}/175 | Rata2={m:.2f} | Pct={pct:.2f}%')
