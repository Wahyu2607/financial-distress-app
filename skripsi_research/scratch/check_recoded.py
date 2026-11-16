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

# Reverse coding for negative items: P2 (col 1), P4 (col 3), P6 (col 5), P8 (col 7), P9 (col 8)
neg_indices = [1, 3, 5, 7, 8]
df_recoded = df_numeric.copy()
for idx in neg_indices:
    col = df_recoded.columns[idx]
    df_recoded[col] = 6 - df_recoded[col]

print("=== REVERSE CODED (POSITIVE ORIENTATION) ===")
recoded_results = []
for i, col in enumerate(likert_cols):
    scores = df_recoded[col]
    total_score = scores.sum()
    max_score = 13 * 5
    pct = (total_score / max_score) * 100
    mean_val = scores.mean()
    q_text = col.split('[')[-1].rstrip(']')
    recoded_results.append({
        'no': i + 1,
        'dimensi': 'Aspek Kemudahan & Antarmuka (UI/UX)' if i < 10 else 'Relevansi Output & Kinerja Fitur (DSS)',
        'pertanyaan': q_text,
        'is_neg': i in neg_indices,
        'total': total_score,
        'max': max_score,
        'mean': mean_val,
        'pct': pct
    })

rec_df = pd.DataFrame(recoded_results)
for idx, r in rec_df.iterrows():
    flag = "(R)" if r['is_neg'] else "   "
    print(f"{r['no']:2d}. {flag} [{r['dimensi'][:12]}] {r['pertanyaan'][:45]}... | Total: {r['total']}/{r['max']} | Mean: {r['mean']:.2f} | Pct: {r['pct']:.2f}%")

dim1_r = rec_df.iloc[0:10]
dim2_r = rec_df.iloc[10:19]
print("\n--- Summary Recoded ---")
print(f"Dimensi 1 (UI/UX - Recoded): Total {dim1_r['total'].sum()}/{dim1_r['max'].sum()} ({dim1_r['total'].sum()/dim1_r['max'].sum()*100:.2f}%), Mean: {dim1_r['mean'].mean():.2f}")
print(f"Dimensi 2 (Fitur & DSS): Total {dim2_r['total'].sum()}/{dim2_r['max'].sum()} ({dim2_r['total'].sum()/dim2_r['max'].sum()*100:.2f}%), Mean: {dim2_r['mean'].mean():.2f}")
print(f"Total Keseluruhan (Recoded): Total {rec_df['total'].sum()}/{rec_df['max'].sum()} ({rec_df['total'].sum()/rec_df['max'].sum()*100:.2f}%), Mean: {rec_df['mean'].mean():.2f}")
