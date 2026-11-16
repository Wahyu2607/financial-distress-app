import pandas as pd
import openpyxl

excel_file = 'Uji Coba (UAT) Sistem Prediksi Financial Distress Manufaktur BEI (Jawaban).xlsx'
wb = openpyxl.load_workbook(excel_file)
print("Sheet names:", wb.sheetnames)

df = pd.read_excel(excel_file)
print("\nDataFrame Shape:", df.shape)
print("\nColumns:")
for i, col in enumerate(df.columns):
    print(f"Col {i}: {col}")

print("\nFirst 3 rows:")
print(df.head(3))
