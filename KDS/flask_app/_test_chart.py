import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database.referral_loaders import load_referral_data
import pandas as pd
import numpy as np
import plotly.express as px

sd = '2025-03-06'
ed = '2026-03-06'
df = load_referral_data(sd, ed)

COL_EDEN_DR = 'Sevk_Eden_Doktor_Ad'
COL_HASTA = 'TOPLAM_HASTA'
COL_SEVK = 'TOPLAM_SEVK'

hasta_map = df.groupby('DOKTOR_ADI')[COL_HASTA].max().to_dict()
eden_sevk = df.groupby(COL_EDEN_DR)[COL_SEVK].sum().reset_index()
eden_sevk[COL_HASTA] = eden_sevk[COL_EDEN_DR].map(hasta_map).fillna(0).astype(float)
eden_sevk[COL_SEVK] = eden_sevk[COL_SEVK].astype(float)
oran_df = eden_sevk.copy()
oran_df['ORAN'] = np.where(
    oran_df[COL_HASTA] > 0,
    (oran_df[COL_SEVK] / oran_df[COL_HASTA] * 100.0),
    0.0,
)
oran_df['ORAN'] = oran_df['ORAN'].replace([np.inf, -np.inf], 0.0).fillna(0.0).astype(float)

oran_scatter = oran_df[(oran_df[COL_HASTA] > 0) & (oran_df['ORAN'] > 0)].copy()
print(f"scatter rows: {len(oran_scatter)}")
print(oran_scatter.head(5).to_string())

fig_oran = px.scatter(
    oran_scatter,
    x=COL_HASTA,
    y=COL_SEVK,
    size='ORAN',
    size_max=40,
    color='ORAN',
    hover_name=COL_EDEN_DR,
    color_continuous_scale='Plasma',
    labels={COL_HASTA: 'TOPLAM_HASTA', COL_SEVK: 'TOPLAM_SEVK', 'ORAN': 'ORAN'},
)
fig_oran.update_layout(
    template='plotly_dark',
    height=500,
    width=900,
    paper_bgcolor='#1a1a2e',
    plot_bgcolor='#1a1a2e',
    xaxis=dict(title='TOPLAM_HASTA'),
    yaxis=dict(title='TOPLAM_SEVK'),
)

html = fig_oran.to_html(full_html=True)
out_path = os.path.join(os.path.dirname(__file__), '_test_scatter.html')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Saved to {out_path}, size={len(html)}")
