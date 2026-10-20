import pandas as pd
import numpy as np

# Load data
df = pd.read_excel('data/datakeuangan.xlsx')
print("Total rows in datakeuangan.xlsx:", len(df))

# Compute X1 - X4
df['X1'] = df['Working Capital'] / df['Total Assets']
df['X2'] = df['Retained Earnings'] / df['Total Assets']
df['EBIT_calc'] = df['EBIT']
df['X3'] = df['EBIT_calc'] / df['Total Assets']
df['X4'] = df['Common Stock Equity'] / df['Total Liabilities Net Minority Interest']

# Distress rule from PDF: Retained Earnings < 0 AND EBIT < 0
df['distress_pdf'] = ((df['Retained Earnings'] < 0) & (df['EBIT'] < 0)).astype(int)
print("Distress count with (RE < 0 and EBIT < 0):")
print(df['distress_pdf'].value_counts())

# Test means for valid rows
valid = df.dropna(subset=['X1', 'X2', 'X3', 'X4', 'distress_pdf']).copy()
print("Valid rows count:", len(valid))
d_group = valid[valid['distress_pdf'] == 1]
n_group = valid[valid['distress_pdf'] == 0]
print(f"Distress count: {len(d_group)}, Non-distress count: {len(n_group)}")

print("Mean Distress:")
print(d_group[['X1', 'X2', 'X3', 'X4']].mean())
print("Mean Non-Distress:")
print(n_group[['X1', 'X2', 'X3', 'X4']].mean())
