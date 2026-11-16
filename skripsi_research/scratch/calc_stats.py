import pandas as pd
import numpy as np

excel_file = 'Uji Coba (UAT) Sistem Prediksi Financial Distress Manufaktur BEI (Jawaban).xlsx'
df = pd.read_excel(excel_file)

# Convert text responses to numeric 1-5
# Values are like "5 (Sangat Setuju)", "4 (Setuju)", etc.
def extract_num(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    return int(s[0])

# Columns 5 to 23
likert_cols = df.columns[5:24]
df_numeric = pd.DataFrame()
for col in likert_cols:
    df_numeric[col] = df[col].apply(extract_num)

print("Numeric conversion verified. Shape:", df_numeric.shape)

# SUS Calculation (Col 5 to 14)
# Odd items (P1, P3, P5, P7, P10 -> indices 0, 2, 4, 6, 9 in df_numeric): score - 1
# Even items (P2, P4, P6, P8, P9 -> indices 1, 3, 5, 7, 8 in df_numeric): 5 - score
sus_scores = []
for idx, row in df_numeric.iloc[:, 0:10].iterrows():
    p1 = row.iloc[0] - 1
    p2 = 5 - row.iloc[1]
    p3 = row.iloc[2] - 1
    p4 = 5 - row.iloc[3]
    p5 = row.iloc[4] - 1
    p6 = 5 - row.iloc[5]
    p7 = row.iloc[6] - 1
    p8 = 5 - row.iloc[7]
    p9 = row.iloc[8] - 1
    p10 = row.iloc[9] - 1
    sus = (p1 + p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9 + p10) * 2.5
    sus_scores.append(sus)

print("SUS Scores per respondent:", sus_scores)
print("Mean SUS Score:", np.mean(sus_scores))

# Now let's calculate regular Likert stats for all 19 items:
results = []
for i, col in enumerate(likert_cols):
    scores = df_numeric[col]
    total_score = scores.sum()
    max_score = 13 * 5
    pct = (total_score / max_score) * 100
    mean_val = scores.mean()
    # Clean question text
    q_text = col.split('[')[-1].rstrip(']')
    results.append({
        'no': i + 1,
        'dimensi': 'Aspek Kemudahan & Antarmuka (UI/UX)' if i < 10 else 'Relevansi Output & Kinerja Fitur (DSS)',
        'pertanyaan': q_text,
        'total': total_score,
        'max': max_score,
        'mean': mean_val,
        'pct': pct
    })

res_df = pd.DataFrame(results)
print("\nLikert Results:")
for idx, r in res_df.iterrows():
    print(f"{r['no']}. [{r['dimensi']}] {r['pertanyaan'][:50]}... | Total: {r['total']}/{r['max']} | Mean: {r['mean']:.2f} | Pct: {r['pct']:.2f}%")

dim1 = res_df.iloc[0:10]
dim2 = res_df.iloc[10:19]
print("\n--- Summary ---")
print(f"Dimensi 1 (UI/UX): Total {dim1['total'].sum()}/{dim1['max'].sum()} ({dim1['total'].sum()/dim1['max'].sum()*100:.2f}%), Rata-rata Skor: {dim1['mean'].mean():.2f}")
print(f"Dimensi 2 (Fitur & DSS): Total {dim2['total'].sum()}/{dim2['max'].sum()} ({dim2['total'].sum()/dim2['max'].sum()*100:.2f}%), Rata-rata Skor: {dim2['mean'].mean():.2f}")
print(f"Total Keseluruhan: Total {res_df['total'].sum()}/{res_df['max'].sum()} ({res_df['total'].sum()/res_df['max'].sum()*100:.2f}%), Rata-rata Skor: {res_df['mean'].mean():.2f}")
