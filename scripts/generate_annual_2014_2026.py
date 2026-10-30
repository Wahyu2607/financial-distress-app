"""
Script untuk menghasilkan file tahunan murni 15 variabel (2014 s.d. 2026)
"""
from pathlib import Path
import pandas as pd

def generate_annual_15_variables():
    # Ambil dari posisi tahunan (Q4) dataset kuartalan 2014-2026
    q_csv = Path('data/dataset_manufaktur_kuartalan_15_variabel_baku_2014_2026.csv')
    df_q = pd.read_csv(q_csv)
    
    # Ambil posisi kuartal Q4 (Annual Audited Position)
    df_annual = df_q[df_q['Kuartal'] == 'Q4'].copy()
    
    cols_15 = [
        'Kode Saham', 'Tahun Laporan', 'EBIT', 'Interest Expense', 'Total Assets',
        'Current Assets', 'Total Liabilities Net Minority Interest', 'Current Liabilities',
        'Common Stock Equity', 'Retained Earnings', 'Working Capital', 'Operating Cash Flow',
        'Total Revenue', 'Net Income', 'Total Debt'
    ]
    
    df_15 = df_annual[cols_15].sort_values(['Kode Saham', 'Tahun Laporan']).reset_index(drop=True)
    
    csv_out = Path('data/dataset_manufaktur_tahunan_15_variabel_2014_2026.csv')
    xlsx_out = Path('data/dataset_manufaktur_tahunan_15_variabel_2014_2026.xlsx')
    
    df_15.to_csv(csv_out, index=False, encoding='utf-8')
    df_15.to_excel(xlsx_out, index=False)
    
    print("="*60)
    print("FILE TAHUNAN 15 VARIABEL (2014-2026) BERHASIL DIBUAT")
    print("="*60)
    print(f"Total Baris Data    : {len(df_15)} baris")
    print(f"Total Emiten        : {df_15['Kode Saham'].nunique()} emiten")
    print(f"Rentang Tahun       : {df_15['Tahun Laporan'].min()} s.d. {df_15['Tahun Laporan'].max()} (13 Tahun)")
    print(f"Lokasi File Excel   : {xlsx_out.resolve()}")
    print(f"Lokasi File CSV     : {csv_out.resolve()}")

if __name__ == "__main__":
    generate_annual_15_variables()
