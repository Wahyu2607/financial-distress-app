import sys
import os
import pandas as pd
import numpy as np

# Load dataset
file_csv = 'data/dataset_manufaktur_tahunan_15_variabel_2014_2026.csv'
file_xlsx = 'data/dataset_manufaktur_tahunan_15_variabel_2014_2026.xlsx'

df = pd.read_csv(file_csv) if os.path.exists(file_csv) else pd.read_excel(file_xlsx)
print(f"Data shape: {df.shape}")
print("Columns:", df.columns.tolist())
print(df.describe())
