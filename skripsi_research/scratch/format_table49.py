import pandas as pd
import numpy as np

excel_file = 'Uji Coba (UAT) Sistem Prediksi Financial Distress Manufaktur BEI (Jawaban).xlsx'
df = pd.read_excel(excel_file)

def extract_num(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    return int(s[0])

likert_cols = df.columns[5:24]
df_numeric = pd.DataFrame()
for col in likert_cols:
    df_numeric[col] = df[col].apply(extract_num)

# In Indonesian academic research:
# Skala Likert 5 tingkat persentase ketercapaian:
# 81% - 100%: Sangat Baik / Sangat Layak / Sangat Setuju
# 61% - 80% : Baik / Layak / Setuju
# 41% - 60% : Cukup Baik / Cukup Layak / Cukup Setuju
# 21% - 40% : Kurang Baik / Kurang Layak / Tidak Setuju
#  0% - 20% : Sangat Kurang Baik / Tidak Layak / Sangat Tidak Setuju

def get_kategori(pct):
    if pct >= 81.0:
        return "Sangat Baik"
    elif pct >= 61.0:
        return "Baik"
    elif pct >= 41.0:
        return "Cukup Baik"
    elif pct >= 21.0:
        return "Kurang Baik"
    else:
        return "Sangat Kurang"

# Let's inspect the questions and stats:
dim1_rows = []
for i in range(10):
    col = likert_cols[i]
    q_text = col.split('[')[-1].rstrip(']')
    scores = df_numeric[col]
    tot = int(scores.sum())
    mx = 13 * 5
    pct = (tot / mx) * 100
    mean_score = scores.mean()
    # Is it negative?
    is_neg = i in [1, 3, 5, 7, 8]
    dim1_rows.append({
        'no': f"A.{i+1}",
        'aspek': q_text,
        'tot': tot,
        'mx': mx,
        'mean': mean_score,
        'pct': pct,
        'kat': get_kategori(pct),
        'is_neg': is_neg
    })

dim2_rows = []
for i in range(10, 19):
    col = likert_cols[i]
    q_text = col.split('[')[-1].rstrip(']')
    scores = df_numeric[col]
    tot = int(scores.sum())
    mx = 13 * 5
    pct = (tot / mx) * 100
    mean_score = scores.mean()
    dim2_rows.append({
        'no': f"B.{i-9}",
        'aspek': q_text,
        'tot': tot,
        'mx': mx,
        'mean': mean_score,
        'pct': pct,
        'kat': get_kategori(pct),
        'is_neg': False
    })

print("=== DIMENSI 1 ===")
for r in dim1_rows:
    print(f"{r['no']} | {r['aspek'][:60]} | {r['tot']} | {r['mx']} | {r['mean']:.2f} | {r['pct']:.2f}% | {r['kat']}")

print("\n=== DIMENSI 2 ===")
for r in dim2_rows:
    print(f"{r['no']} | {r['aspek'][:60]} | {r['tot']} | {r['mx']} | {r['mean']:.2f} | {r['pct']:.2f}% | {r['kat']}")
