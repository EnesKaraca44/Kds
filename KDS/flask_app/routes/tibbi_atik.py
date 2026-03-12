from flask import Blueprint, render_template
import pandas as pd
import plotly.express as px
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required
from database.tıbbi_atık_sorgular import tibbi_atik_verisi_yukle
from routes.dashboard import get_date_range

tibbi_atik_bp = Blueprint('tibbi_atik', __name__)


@tibbi_atik_bp.route('/tibbi-atik')
@login_required
def tibbi_atik():
    sd, ed = get_date_range()
    df = tibbi_atik_verisi_yukle(sd, ed)

    if df.empty:
        return render_template('tibbi_atik.html', start_date=sd, end_date=ed, no_data=True)

    df.columns = [c.upper().strip() for c in df.columns]
    aylar = ['OCAK', 'ŞUBAT', 'MART', 'NİSAN', 'MAYIS', 'HAZİRAN',
             'TEMMUZ', 'AĞUSTOS', 'EYLÜL', 'EKİM', 'KASIM', 'ARALIK']
    mevcut_aylar = [ay for ay in aylar if ay in df.columns]

    total_val = df['TOPLAM'].sum()
    aylik_ort = total_val / len(mevcut_aylar) if mevcut_aylar else 0

    trend_df = df[mevcut_aylar].sum().reset_index()
    trend_df.columns = ['AY', 'MIKTAR']
    fig_trend = px.line(trend_df, x='AY', y='MIKTAR', markers=True, title="Aylık Toplam Atık Seyri")
    fig_trend.update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    fig_pie = px.pie(df.nlargest(10, 'TOPLAM'), values='TOPLAM', names='HESAP_PLANI_TANIMI',
                     title="En Çok Atık Üreten 10 Birim", hole=0.3)
    fig_pie.update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    fig_heat = px.imshow(df.set_index('HESAP_PLANI_TANIMI')[mevcut_aylar], color_continuous_scale='Reds', aspect="auto")
    fig_heat.update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    charts = {
        'fig_trend': fig_trend.to_html(full_html=False, include_plotlyjs=False),
        'fig_pie': fig_pie.to_html(full_html=False, include_plotlyjs=False),
        'fig_heat': fig_heat.to_html(full_html=False, include_plotlyjs=False),
    }

    return render_template('tibbi_atik.html',
        start_date=sd, end_date=ed, no_data=False,
        total_val=total_val, aylik_ort=aylik_ort, birim_sayisi=len(df),
        charts=charts,
    )
