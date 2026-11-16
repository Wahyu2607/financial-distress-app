import sys
import os
sys.path.insert(0, os.path.abspath('.'))
import pandas as pd
from src.calculations import build_features_p1, build_features_p2, build_distress_target

df = pd.read_csv('data/dataset_manufaktur_tahunan_15_variabel_2014_2026.csv')
y, desc = build_distress_target(df, method='predictive_t1')
print("Target description:", desc)
print("Target counts:\n", y.value_counts())

X_p1 = build_features_p1(df)
print("X_p1 shape:", X_p1.shape)
print("X_p1 columns:", X_p1.columns.tolist())
print(X_p1.head(2))

X_p2 = build_features_p2(df)
print("X_p2 shape:", X_p2.shape)
print("X_p2 columns:", X_p2.columns.tolist())
print(X_p2.head(2))
