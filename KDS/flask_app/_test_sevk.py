import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database.referral_loaders import load_referral_data
import pandas as pd
import numpy as np

sd = '2025-03-06'
ed = '2026-03-06'
df = load_referral_data(sd, ed)
print(f"df shape: {df.shape}")
print(f"df columns: {list(df.columns)}")
print(f"df dtypes:\n{df.dtypes}")
print()

if df.empty:
    print("NO DATA!")
    sys.exit()

print(f"df head:\n{df.head(3).to_string()}")
print()

COL_EDEN_DR = 'Sevk_Eden_Doktor_Ad'
COL_HASTA = 'TOPLAM_HASTA'
COL_SEVK = 'TOPLAM_SEVK'

print(f"TOPLAM_HASTA unique values (first 20): {sorted(df[COL_HASTA].unique())[:20]}")
print(f"TOPLAM_HASTA > 0 count: {(df[COL_HASTA] > 0).sum()}")
print(f"TOPLAM_SEVK > 0 count: {(df[COL_SEVK] > 0).sum()}")
print()

hasta_map = df.groupby('DOKTOR_ADI')[COL_HASTA].max().to_dict()
print(f"hasta_map size: {len(hasta_map)}")
print(f"hasta_map sample (first 5):")
for i, (k, v) in enumerate(hasta_map.items()):
    if i >= 5:
        break
    print(f"  {k}: {v}")
print()

eden_sevk = df.groupby(COL_EDEN_DR)[COL_SEVK].sum().reset_index()
eden_sevk[COL_HASTA] = eden_sevk[COL_EDEN_DR].map(hasta_map).fillna(0).astype(float)
eden_sevk[COL_SEVK] = eden_sevk[COL_SEVK].astype(float)

eden_sevk['ORAN'] = np.where(
    eden_sevk[COL_HASTA] > 0,
    (eden_sevk[COL_SEVK] / eden_sevk[COL_HASTA] * 100.0),
    0.0,
)

print(f"eden_sevk rows: {len(eden_sevk)}")
print(f"eden_sevk HASTA>0: {(eden_sevk[COL_HASTA]>0).sum()}")
print(f"eden_sevk ORAN>0: {(eden_sevk['ORAN']>0).sum()}")
print()
print(f"eden_sevk (HASTA>0) sample:")
sample = eden_sevk[eden_sevk[COL_HASTA] > 0].head(10)
print(sample.to_string())
print()
print(f"eden_sevk (HASTA==0) sample:")
sample0 = eden_sevk[eden_sevk[COL_HASTA] == 0].head(5)
print(sample0.to_string())
