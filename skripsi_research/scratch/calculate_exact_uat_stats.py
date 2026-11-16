import openpyxl, re
import numpy as np

wb = openpyxl.load_workbook('Uji Coba (UAT) Sistem Prediksi Financial Distress Manufaktur BEI (Jawaban).xlsx')
sheet = wb.active

headers = [sheet.cell(1, c).value for c in range(1, sheet.max_column + 1)]
n_resp = sheet.max_row - 1
print(f"Total Responden: {n_resp}")

# Collect data
rows = []
for r in range(2, sheet.max_row + 1):
    vals = []
    for c in range(6, 25): # 19 questions
        raw = str(sheet.cell(r, c).value)
        m = re.match(r'(\d+)', raw)
        vals.append(int(m.group(1)) if m else 0)
    
    kritik = sheet.cell(r, 25).value
    manfaat = sheet.cell(r, 26).value
    rows.append({
        'name': sheet.cell(r, 2).value,
        'scores': vals,
        'kritik': kritik,
        'manfaat': manfaat
    })

# Compute raw and recoded stats
# Dimensi A: indices 0..9 (Q1..Q10)
# Negative items in Dimensi A: Q2 (idx 1), Q4 (idx 3), Q6 (idx 5), Q8 (idx 7), Q9 (idx 8)
neg_indices = {1, 3, 5, 7, 8}

print("\n" + "="*80)
print(f"{'No':<5}{'Pernyataan Kuesioner':<60}{'Raw Tot':<9}{'Rec Tot':<9}{'Rata2':<8}{'Pct':<9}{'Kategori'}")
print("="*80)

dimA_rec_scores = []
dimB_scores = []

all_table_rows = []

for i in range(19):
    q_header = headers[5 + i]
    m = re.search(r'\[(.*?)\]', q_header)
    q_text = m.group(1) if m else q_header
    
    raw_vals = [r['scores'][i] for r in rows]
    raw_tot = sum(raw_vals)
    raw_mean = np.mean(raw_vals)
    
    is_neg = (i in neg_indices)
    
    if is_neg:
        rec_vals = [6 - v for v in raw_vals]
        rec_tot = sum(rec_vals)
        rec_mean = np.mean(rec_vals)
        pct = (rec_tot / (n_resp * 5)) * 100
        mean_used = rec_mean
        tot_used = rec_tot
    else:
        rec_vals = raw_vals
        rec_tot = raw_tot
        rec_mean = raw_mean
        pct = (raw_tot / (n_resp * 5)) * 100
        mean_used = raw_mean
        tot_used = raw_tot
        
    if i < 10:
        dimA_rec_scores.append(rec_vals)
    else:
        dimB_scores.append(raw_vals)
        
    # Kategori
    if pct >= 81.0:
        kat = "Sangat Baik"
    elif pct >= 61.0:
        kat = "Baik"
    elif pct >= 41.0:
        kat = "Cukup Baik"
    elif pct >= 21.0:
        kat = "Kurang Baik"
    else:
        kat = "Tidak Baik"
        
    num_str = f"A.{i+1}*" if is_neg else (f"A.{i+1}" if i < 10 else f"B.{i-9}")
    
    all_table_rows.append({
        'num': num_str,
        'text': q_text,
        'raw_tot': raw_tot,
        'tot_used': tot_used,
        'mean_used': mean_used,
        'pct': pct,
        'kat': kat,
        'is_neg': is_neg
    })
    
    print(f"{num_str:<5}{q_text[:58]:<60}{raw_tot:<9}{tot_used:<9}{mean_used:<8.2f}{pct:<9.2f}%{kat}")

# Subtotals
# Dimensi A
dimA_tot = sum([r['tot_used'] for r in all_table_rows[:10]])
dimA_max = n_resp * 5 * 10 # 35 * 50 = 1750
dimA_mean = dimA_tot / (n_resp * 10)
dimA_pct = (dimA_tot / dimA_max) * 100
dimA_kat = "Sangat Baik" if dimA_pct >= 81 else ("Baik" if dimA_pct >= 61 else "Cukup Baik")

# Dimensi B
dimB_tot = sum([r['tot_used'] for r in all_table_rows[10:]])
dimB_max = n_resp * 5 * 9 # 35 * 45 = 1575
dimB_mean = dimB_tot / (n_resp * 9)
dimB_pct = (dimB_tot / dimB_max) * 100
dimB_kat = "Sangat Baik" if dimB_pct >= 81 else ("Baik" if dimB_pct >= 61 else "Cukup Baik")

# Total Agregat
grand_tot = dimA_tot + dimB_tot
grand_max = dimA_max + dimB_max # 1750 + 1575 = 3325
grand_mean = grand_tot / (n_resp * 19)
grand_pct = (grand_tot / grand_max) * 100
grand_kat = "Sangat Baik" if grand_pct >= 81 else ("Baik" if grand_pct >= 61 else "Cukup Baik")

print("\n" + "="*80)
print(f"SUBTOTAL DIMENSI A (Kemudahan & Antarmuka): Tot={dimA_tot}/{dimA_max} | Rata-rata={dimA_mean:.2f} | Pct={dimA_pct:.2f}% | Kat={dimA_kat}")
print(f"SUBTOTAL DIMENSI B (Relevansi & Fitur DSS): Tot={dimB_tot}/{dimB_max} | Rata-rata={dimB_mean:.2f} | Pct={dimB_pct:.2f}% | Kat={dimB_kat}")
print(f"TOTAL REKAPITULASI AKSEPTANSI (n=35): Tot={grand_tot}/{grand_max} | Rata-rata={grand_mean:.2f} | Pct={grand_pct:.2f}% | Kat={grand_kat}")
print("="*80)

# Standard SUS Score (0-100)
# SUS Formula: for odd questions (0, 2, 4, 6, 9), contribution = score - 1
# for even questions (1, 3, 5, 7, 8), contribution = 5 - score
# sum contributions * 2.5
sus_scores = []
for r in rows:
    sc = r['scores'][:10]
    c1 = sc[0] - 1
    c2 = 5 - sc[1]
    c3 = sc[2] - 1
    c4 = 5 - sc[3]
    c5 = sc[4] - 1
    c6 = 5 - sc[5]
    c7 = sc[6] - 1
    c8 = 5 - sc[7]
    c9 = 5 - sc[8]
    c10 = sc[9] - 1
    sus = (c1 + c2 + c3 + c4 + c5 + c6 + c7 + c8 + c9 + c10) * 2.5
    sus_scores.append(sus)

avg_sus = np.mean(sus_scores)
std_sus = np.std(sus_scores)
print(f"\nSKOR STANDAR SYSTEM USABILITY SCALE (SUS):")
print(f"Rata-rata Skor SUS: {avg_sus:.2f} / 100 (Standar Deviasi: {std_sus:.2f})")
# SUS interpretation: > 68 is above average, 70-80 is Acceptable / Grade B / Good.

# Qualitative analysis
print("\n=== UMPAN BALIK KUALITATIF RESPONDEN ===")
manfaat_counts = {}
for r in rows:
    m = r['manfaat']
    if m:
        m_clean = m.strip()
        # categorise
        m_lower = m_clean.lower()
        if 'dashboard' in m_lower or 'prediksi' in m_lower:
            cat = 'Dashboard Prediksi & Visualisasi Risiko'
        elif 'input' in m_lower:
            cat = 'Fitur Input Data & Tarik API'
        elif 'evaluasi' in m_lower or 'perbandingan' in m_lower:
            cat = 'Fitur Evaluasi & Komparasi Tiga Model'
        else:
            cat = 'Tampilan Antarmuka Umum'
        manfaat_counts[cat] = manfaat_counts.get(cat, 0) + 1

print("Tampilan Paling Bermanfaat (Kategori):", manfaat_counts)

# Criticisms & Suggestions
saran_list = []
for r in rows:
    k = r['kritik']
    if k and str(k).strip() not in ['-', 'tidak ada', 'tidak', 'Belum ada', 'None']:
        saran_list.append(str(k).strip())

print(f"\nSaran / Kritik Konstruktif yang Diberikan ({len(saran_list)} responden):")
for s in saran_list:
    print(f"  * {s}")
