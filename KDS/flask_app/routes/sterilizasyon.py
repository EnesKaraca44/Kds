from flask import Blueprint, render_template
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required
from database.sterilizasyon_sorgular import sterilizasyon_verisi_yukle
from routes.dashboard import get_date_range

sterilizasyon_bp = Blueprint('sterilizasyon', __name__)


@sterilizasyon_bp.route('/sterilizasyon')
@login_required
def sterilizasyon():
    sd, ed = get_date_range()
    df_all = sterilizasyon_verisi_yukle(sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d'))

    if df_all.empty:
        return render_template('sterilizasyon.html', start_date=sd, end_date=ed, no_data=True)

    df_grouped = df_all.groupby('ServisAdi').agg({
        'Toplam_Maliyet': 'sum', 'Toplam_Paket': 'sum', 'Hasta_Sayisi': 'sum'
    }).reset_index()
    df_grouped['Birim_Maliyet'] = df_grouped.apply(lambda x: x['Toplam_Maliyet'] / x['Toplam_Paket'] if x['Toplam_Paket'] > 0 else 0, axis=1)
    df_grouped['Hasta_Basi_Maliyet'] = df_grouped.apply(lambda x: x['Toplam_Maliyet'] / x['Hasta_Sayisi'] if x['Hasta_Sayisi'] > 0 else 0, axis=1)

    t_maliye = df_grouped['Toplam_Maliyet'].sum()
    t_paket = df_grouped['Toplam_Paket'].sum()
    t_hasta = df_grouped['Hasta_Sayisi'].sum()

    top_clinics = df_grouped.nlargest(15, 'Toplam_Maliyet')
    fig_bar = px.bar(top_clinics, x='ServisAdi', y='Toplam_Maliyet', color='Birim_Maliyet',
                     color_continuous_scale='Reds', title="Maliyet Lideri İlk 15 Klinik")
    fig_bar.update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    avg_paket_maliyet = df_grouped['Birim_Maliyet'].mean()
    avg_hasta_maliyet = df_grouped['Hasta_Basi_Maliyet'].mean()
    fig_smart = px.scatter(df_grouped, x="Birim_Maliyet", y="Hasta_Basi_Maliyet", size="Toplam_Maliyet", color="ServisAdi",
                           title="Birim Paket vs. Hasta Başı Maliyet")
    fig_smart.add_vline(x=avg_paket_maliyet, line_dash="dash", line_color="gray")
    fig_smart.add_hline(y=avg_hasta_maliyet, line_dash="dash", line_color="gray")
    fig_smart.update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    charts = {
        'fig_bar': fig_bar.to_html(full_html=False, include_plotlyjs=False),
        'fig_smart': fig_smart.to_html(full_html=False, include_plotlyjs=False),
    }

    return render_template('sterilizasyon.html',
        start_date=sd, end_date=ed, no_data=False,
        t_maliye=t_maliye, t_paket=t_paket, t_hasta=t_hasta,
        charts=charts,
    )
