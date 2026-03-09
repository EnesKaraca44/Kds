from flask import Blueprint, render_template, request, session
from datetime import date, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required
from database.doctor_point import load_doctor_points_data
from routes.dashboard import get_date_range

hekim_puan_bp = Blueprint('hekim_puan', __name__)


@hekim_puan_bp.route('/hekim-puan')
@login_required
def hekim_puan():
    sd, ed = get_date_range()

    df_raw = load_doctor_points_data(sd, ed)
    if df_raw is None or df_raw.empty:
        return render_template('hekim_puan.html', start_date=sd, end_date=ed, no_data=True)

    df = df_raw.copy()
    df['TETKIK_TOPLAM_PUAN'] = pd.to_numeric(df['TETKIK_TOPLAM_PUAN'], errors='coerce').fillna(0)
    df['TETKIK_ADET'] = pd.to_numeric(df['TETKIK_ADET'], errors='coerce').fillna(0)
    df['TETKIK_BIRIM_UCRET'] = pd.to_numeric(df['TETKIK_BIRIM_UCRET'], errors='coerce').fillna(0)
    df['TOPLAM_GELIR'] = df['TETKIK_ADET'] * df['TETKIK_BIRIM_UCRET']

    hekim_perf = df.groupby('TETKIK_DOKTOR_ADI').agg({
        'TETKIK_TARIHI': 'nunique', 'HASTA_GELIS_NO': 'nunique',
        'TETKIK_TOPLAM_PUAN': 'sum', 'TOPLAM_GELIR': 'sum'
    }).reset_index()
    hekim_perf.columns = ['Hekim', 'Calisma_Gun', 'Toplam_Hasta', 'Toplam_Puan', 'Toplam_Gelir']
    hekim_perf['Hasta_Basi_Gelir'] = (hekim_perf['Toplam_Gelir'] / hekim_perf['Toplam_Hasta']).round(2)

    total_puan = hekim_perf['Toplam_Puan'].sum()
    total_gelir = hekim_perf['Toplam_Gelir'].sum()
    total_hasta = hekim_perf['Toplam_Hasta'].sum()
    avg_calisma_gun = hekim_perf['Calisma_Gun'].mean()
    genel_cmi_gelir = total_gelir / total_hasta if total_hasta > 0 else 0

    # Query Parameters
    sort_by = request.args.get('sort', 'Toplam_Puan')
    limit = request.args.get('limit', 10, type=int)

    # Validasyon
    valid_sorts = ['Toplam_Puan', 'Toplam_Gelir', 'Hasta_Basi_Gelir']
    if sort_by not in valid_sorts:
        sort_by = 'Toplam_Puan'

    # Tab 1: Finansal Performans (Top/Bottom Bar Charts)
    top_df = hekim_perf.nlargest(limit, sort_by).sort_values(sort_by, ascending=True)
    fig_max = px.bar(top_df, x=sort_by, y='Hekim', orientation='h',
                     title=f"En Yüksek {sort_by} Üretenler",
                     color=sort_by, color_continuous_scale='Greens', text_auto='.3s')
    
    if sort_by in ['Toplam_Gelir', 'Hasta_Basi_Gelir']:
        fig_max.update_layout(xaxis_tickprefix="₺ ")
    fig_max.update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    bottom_df = hekim_perf.nsmallest(limit, sort_by).sort_values(sort_by, ascending=False)
    fig_min = px.bar(bottom_df, x=sort_by, y='Hekim', orientation='h',
                     title=f"En Düşük {sort_by} Üretenler",
                     color=sort_by, color_continuous_scale='Reds', text_auto='.3s')
    
    if sort_by in ['Toplam_Gelir', 'Hasta_Basi_Gelir']:
        fig_min.update_layout(xaxis_tickprefix="₺ ")
    fig_min.update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    # Tab 2: Pareto
    pareto_df = hekim_perf.sort_values("Toplam_Gelir", ascending=False).copy()
    pareto_df['Kumulatif_Yuzde'] = 100 * pareto_df['Toplam_Gelir'].cumsum() / total_gelir
    fig_p = px.bar(pareto_df, x='Hekim', y='Toplam_Gelir', text_auto='.2s')
    fig_p.add_scatter(x=pareto_df['Hekim'], y=pareto_df['Kumulatif_Yuzde'], name='Kümülatif %', yaxis='y2', line=dict(color="#f39c12"))
    fig_p.update_layout(yaxis2=dict(anchor='x', overlaying='y', side='right', range=[0, 105]), yaxis_tickprefix="₺ ",
                        template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    # Tab 2: CMI Scatter
    fig_cmi = px.scatter(hekim_perf, x="Toplam_Hasta", y="Hasta_Basi_Gelir", size="Toplam_Puan",
                         color="Hasta_Basi_Gelir", hover_name="Hekim", text="Hekim", color_continuous_scale='Viridis')
    fig_cmi.update_traces(textposition='top center')
    fig_cmi.update_yaxes(tickprefix="₺ ")
    fig_cmi.add_hline(y=genel_cmi_gelir, line_dash="dash", line_color="red", annotation_text="Kurum CMI Ortalaması")
    fig_cmi.update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    charts = {
        'fig_max': fig_max.to_html(full_html=False, include_plotlyjs=False),
        'fig_min': fig_min.to_html(full_html=False, include_plotlyjs=False),
        'fig_pareto': fig_p.to_html(full_html=False, include_plotlyjs=False),
        'fig_cmi': fig_cmi.to_html(full_html=False, include_plotlyjs=False),
    }

    return render_template('hekim_puan.html',
        start_date=sd, end_date=ed, no_data=False,
        total_puan=total_puan, total_gelir=total_gelir,
        total_hasta=total_hasta, aktif_hekim=len(hekim_perf),
        avg_calisma_gun=avg_calisma_gun, genel_cmi_gelir=genel_cmi_gelir,
        charts=charts, current_sort=sort_by, current_limit=limit
    )
