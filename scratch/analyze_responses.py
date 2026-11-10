import pandas as pd

excel_file = 'Uji Coba (UAT) Sistem Prediksi Financial Distress Manufaktur BEI (Jawaban).xlsx'
df = pd.read_excel(excel_file)

print("Demographics:")
print(df[['Nama Lengkap / Inisial Responden', 'usia', 'Kategori / Latar Belakang Profesi']])

print("\nValue types in Likert columns:")
for i in range(5, 24):
    col_name = df.columns[i]
    print(f"\n--- Col {i}: {col_name[:60]}... ---")
    print(df[col_name].value_counts())
