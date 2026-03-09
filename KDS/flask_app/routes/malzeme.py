from flask import Blueprint, render_template
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required
from database.stock_loaders import load_stock_consumption_data
from routes.dashboard import get_date_range

malzeme_bp = Blueprint('malzeme', __name__)


@malzeme_bp.route('/malzeme')
@login_required
def malzeme():
    sd, ed = get_date_range()
    df_raw = load_stock_consumption_data(sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d'))

    if df_raw is None or df_raw.empty:
        return render_template('malzeme.html', start_date=sd, end_date=ed, no_data=True)

    df = df_raw.copy()
    df['dusumTarih'] = pd.to_datetime(df['dusumTarih']).dt.date
    df['toplam'] = pd.to_numeric(df['toplam'], errors='coerce').fillna(0).round(2)
    df['dusumMiktar'] = pd.to_numeric(df['dusumMiktar'], errors='coerce').fillna(0).round(0)

    daily = df.groupby('dusumTarih')['dusumMiktar'].sum().reset_index().sort_values('dusumTarih')
    daily['5_Gunluk_Ort'] = daily['dusumMiktar'].rolling(window=5).mean().round(1)

    # Trend
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(x=daily['dusumTarih'], y=daily['dusumMiktar'], name='Günlük Tüketim', marker_color='#3498db'))
    fig_trend.add_trace(go.Scatter(x=daily['dusumTarih'], y=daily['5_Gunluk_Ort'], name='5 Günlük Ort.',
                                   line=dict(color='#e74c3c', width=3, dash='dot')))
    fig_trend.update_layout(xaxis_title="Tarih", yaxis_title="Adet", template='plotly_white',
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    # Branş dağılımı
    branch_sum = df.groupby('bransAdi')['toplam'].sum().reset_index().sort_values('toplam', ascending=False).head(10)
    fig_br = px.bar(branch_sum, x='toplam', y='bransAdi', orientation='h', title="En Çok Tüketen 10 Branş (₺)",
                    color='toplam', color_continuous_scale='Reds')
    fig_br.update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    # Hekim scatter
    doc_perf = df.groupby('doktorAdSoyad').agg({'dusumMiktar': 'sum', 'toplam': 'sum', 'hastaAdSoyad': 'nunique'}).reset_index()
    doc_perf['hasta_basi_maliyet'] = (doc_perf['toplam'] / doc_perf['hastaAdSoyad']).round(2)
    fig_sc = px.scatter(doc_perf, x='hastaAdSoyad', y='toplam', size='hasta_basi_maliyet', color='doktorAdSoyad',
                        title="Maliyet & Hasta Sayısı İlişkisi")
    fig_sc.update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    charts = {
        'fig_trend': fig_trend.to_html(full_html=False, include_plotlyjs=False),
        'fig_branch': fig_br.to_html(full_html=False, include_plotlyjs=False),
        'fig_scatter': fig_sc.to_html(full_html=False, include_plotlyjs=False),
    }

    return render_template('malzeme.html',
        start_date=sd, end_date=ed, no_data=False,
        toplam_tuketim=df['dusumMiktar'].sum(), tekil_hasta=df['hastaAdSoyad'].nunique(),
        farkli_malzeme=df['stokAd'].nunique(), toplam_tutar=df['toplam'].sum(),
        charts=charts,
    )
