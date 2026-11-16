import pandas as pd

excel_file = 'Uji Coba (UAT) Sistem Prediksi Financial Distress Manufaktur BEI (Jawaban).xlsx'
df = pd.read_excel(excel_file)

print("Kritik & Saran (Col 24):")
for i, val in enumerate(df.iloc[:, 24]):
    if pd.notna(val):
        print(f"[{i+1}] {val}")

print("\nTampilan Paling Bermanfaat (Col 25):")
for i, val in enumerate(df.iloc[:, 25]):
    if pd.notna(val):
        print(f"[{i+1}] {val}")
