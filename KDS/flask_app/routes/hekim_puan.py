from flask import Blueprint, render_template, request, session
from datetime import date, timedelta
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required
from database.hekim_puan_sorgular import hekim_puan_verisi_yukle
from routes.dashboard import get_date_range

hekim_puan_bp = Blueprint('hekim_puan', __name__)

PAGE_SQL_KODLARI = ["hekim_puan.hekim_puan_verisi_yukle"]


def _tr_number(v, decimals=2):
    """Binlik ayırıcı nokta, ondalık virgül (tr-TR)."""
    if v is None or pd.isna(v):
        return "-"
    fmt = f"{{:,.{decimals}f}}"
    s = fmt.format(float(v))
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _bar_value_labels(series, sort_key):
    if sort_key in ("Toplam_Gelir", "Hasta_Basi_Gelir"):
        return [f"₺ {_tr_number(x, 2)}" for x in series]
    return [_tr_number(x, 2) for x in series]


def _apply_hekim_puan_from_api(df):
    """
    HEKIM_PUAN_TAB1: Toplampuan bazı satırlarda 0 iken mesaiIciPuan/mesaiDisiPuan dolu olabilir.
    Ayrıca sütun adı varyasyonlarını tek TETKIK_TOPLAM_PUAN altında toplar.
    """
    puan_col = None
    for c in ("TETKIK_TOPLAM_PUAN", "Toplampuan", "toplampuan", "TOPLAMPUAN"):
        if c in df.columns:
            puan_col = c
            break
    base = pd.to_numeric(df[puan_col], errors="coerce").fillna(0) if puan_col else pd.Series(0.0, index=df.index)
    if "mesaiIciPuan" in df.columns and "mesaiDisiPuan" in df.columns:
        mesai = pd.to_numeric(df["mesaiIciPuan"], errors="coerce").fillna(0) + pd.to_numeric(
            df["mesaiDisiPuan"], errors="coerce"
        ).fillna(0)
        df["TETKIK_TOPLAM_PUAN"] = np.where(base > 0, base, mesai)
    else:
        df["TETKIK_TOPLAM_PUAN"] = base
    return df


@hekim_puan_bp.route('/hekim-puan')
@login_required
def hekim_puan():
    sd, ed = get_date_range()

    df_raw = hekim_puan_verisi_yukle(sd, ed)
    if df_raw is None or df_raw.empty:
        # scripts bloğu hekim_stats_dict vb. bekliyor; Undefined -> tojson TypeError olur
        return render_template(
            "hekim_puan.html",
            start_date=sd,
            end_date=ed,
            no_data=True,
            hekim_stats_dict={},
            hekim_hizmet_dict={},
            genel_cmi_gelir=0.0,
            total_gelir=0.0,
            aktif_hekim=0,
            page_sql_kodlari=PAGE_SQL_KODLARI,
        )

    df = df_raw.copy()
    
    # API artık doğru alias'larla dönüyor, bu yüzden sadece ufak eksik kontrolleri yapıyoruz
    if 'TETKIK_TARIHI' not in df.columns:
        df['TETKIK_TARIHI'] = sd
    if 'TETKIK_ADET' not in df.columns:
        df['TETKIK_ADET'] = 1

    df = _apply_hekim_puan_from_api(df)
    df['TETKIK_ADET'] = pd.to_numeric(df.get('TETKIK_ADET', 1), errors='coerce').fillna(0)
    df['TETKIK_BIRIM_UCRET'] = pd.to_numeric(df.get('TETKIK_BIRIM_UCRET', 0), errors='coerce').fillna(0)
    
    if 'TOPLAM_GELIR' not in df.columns:
        df['TOPLAM_GELIR'] = df['TETKIK_ADET'] * df['TETKIK_BIRIM_UCRET']
    else:
        df['TOPLAM_GELIR'] = pd.to_numeric(df['TOPLAM_GELIR'], errors='coerce').fillna(0)

    # API artık RawData (ham veri) dönüyorsa, gruplamayı başarıyla yapabiliriz
    if 'TETKIK_DOKTOR_ADI' not in df.columns:
         df.rename(columns={df.columns[0]: 'TETKIK_DOKTOR_ADI'}, inplace=True)

    hekim_perf = df.groupby('TETKIK_DOKTOR_ADI').agg({
        'TETKIK_TARIHI': 'nunique', 
        'HASTA_GELIS_NO': 'nunique',
        'TETKIK_TOPLAM_PUAN': 'sum', 
        'TOPLAM_GELIR': 'sum'
    }).reset_index()
    hekim_perf.columns = ['Hekim', 'Calisma_Gun', 'Toplam_Hasta', 'Toplam_Puan', 'Toplam_Gelir']
    hekim_perf['Hasta_Basi_Gelir'] = (hekim_perf['Toplam_Gelir'] / hekim_perf['Toplam_Hasta']).round(2).replace([np.inf, -np.inf], 0).fillna(0)

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
                     title="",
                     color=sort_by, color_continuous_scale='Greens')
    fig_max.update_traces(
        text=_bar_value_labels(top_df[sort_by], sort_by),
        texttemplate='%{text}',
        textposition='inside',
        insidetextanchor='end',
        textfont=dict(color='white', size=12),
    )
    axis_title = {'Toplam_Puan': 'Toplam puan', 'Toplam_Gelir': 'Toplam gelir (₺)', 'Hasta_Basi_Gelir': 'Hasta başı gelir (₺)'}.get(sort_by, sort_by)
    if sort_by in ['Toplam_Gelir', 'Hasta_Basi_Gelir']:
        fig_max.update_layout(xaxis_tickprefix="")
    fig_max.update_layout(
        template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title=axis_title,
    )

    bottom_df = hekim_perf.nsmallest(limit, sort_by).sort_values(sort_by, ascending=True)
    fig_min = px.bar(bottom_df, x=sort_by, y='Hekim', orientation='h', title="")
    fig_min.update_traces(
        marker_color='#fca5a5',
        marker_line=dict(color='#f87171', width=1),
        text=_bar_value_labels(bottom_df[sort_by], sort_by),
        texttemplate='%{text}',
        textposition='inside',
        insidetextanchor='end',
        textfont=dict(color='#7f1d1d', size=12),
    )
    if sort_by in ['Toplam_Gelir', 'Hasta_Basi_Gelir']:
        fig_min.update_layout(xaxis_tickprefix="")
    fig_min.update_layout(
        template='plotly_white',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title=axis_title,
        showlegend=False,
    )

    # Tab 2: Pareto
    pareto_df = hekim_perf.sort_values("Toplam_Gelir", ascending=False).copy()
    pareto_df['Kumulatif_Yuzde'] = 100 * pareto_df['Toplam_Gelir'].cumsum() / total_gelir
    fig_p = px.bar(pareto_df, x='Hekim', y='Toplam_Gelir', text_auto='.2s')
    fig_p.add_scatter(x=pareto_df['Hekim'], y=pareto_df['Kumulatif_Yuzde'], name='Kümülatif %', yaxis='y2', line=dict(color="#f39c12"))
    fig_p.update_layout(yaxis2=dict(anchor='x', overlaying='y', side='right', range=[0, 105]), yaxis_tickprefix="",
                        template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    # Tab 2: CMI Scatter
    fig_cmi = px.scatter(hekim_perf, x="Toplam_Hasta", y="Hasta_Basi_Gelir", size="Toplam_Puan",
                         color="Hasta_Basi_Gelir", hover_name="Hekim", text="Hekim", color_continuous_scale='Viridis')
    fig_cmi.update_traces(textposition='top center')
    fig_cmi.update_yaxes(tickprefix="")
    fig_cmi.add_hline(y=genel_cmi_gelir, line_dash="dash", line_color="red", annotation_text="")
    fig_cmi.update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    # 1. Hizmet & Puan Analizi
    hizmet_dagilimi = df.groupby(['TETKIK_DOKTOR_ADI', 'TETKIK_ADI']).agg({
        'TETKIK_ADET': 'sum',
        'TETKIK_TOPLAM_PUAN': 'sum',
        'TOPLAM_GELIR': 'sum'
    }).reset_index()
    
    hekim_hizmet_dict = {}
    for hekim in hekim_perf['Hekim'].unique():
        hizmetler = hizmet_dagilimi[hizmet_dagilimi['TETKIK_DOKTOR_ADI'] == hekim]
        hekim_hizmet_dict[hekim] = hizmetler.to_dict('records')
        
    hekim_stats_dict = hekim_perf.set_index('Hekim').to_dict('index')

    # 2. Detaylı Liste
    df_detayli = df[['TETKIK_DOKTOR_ADI', 'HASTA_ADI_SOYADI', 'TETKIK_ADI', 'TETKIK_ADET', 'TETKIK_TOPLAM_PUAN', 'TOPLAM_GELIR', 'TETKIK_TARIHI']].copy()
    if pd.api.types.is_datetime64_any_dtype(df_detayli['TETKIK_TARIHI']):
        df_detayli['TETKIK_TARIHI'] = df_detayli['TETKIK_TARIHI'].dt.strftime('%Y-%m-%d')
    else:
        df_detayli['TETKIK_TARIHI'] = df_detayli['TETKIK_TARIHI'].astype(str)
        
    df_detayli.fillna('', inplace=True)
    df_detayli_records = df_detayli.to_dict('records')

    # 3. Akıllı Kıyas & Risk Analizi
    def get_risk_status(row):
        if row['Hasta_Basi_Gelir'] > genel_cmi_gelir * 1.2:
            return '🌟 Premium Hizmet Üretimi'
        elif row['Hasta_Basi_Gelir'] < genel_cmi_gelir * 0.8:
            return '⚠️ Düşük CMI Riski'
        else:
            return '✅ Dengeli'
            
    hekim_perf['Durum_Analizi'] = hekim_perf.apply(get_risk_status, axis=1)
    hekim_perf_records = hekim_perf.to_dict('records')

    # Akran Grafik
    fig_peer = px.bar(hekim_perf, x='Hekim', y='Hasta_Basi_Gelir', 
                      title="",
                      color='Hasta_Basi_Gelir', color_continuous_scale='Spectral')
    fig_peer.update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    charts = {
        'fig_max': fig_max.to_html(full_html=False, include_plotlyjs=False),
        'fig_min': fig_min.to_html(full_html=False, include_plotlyjs=False),
        'fig_pareto': fig_p.to_html(full_html=False, include_plotlyjs=False),
        'fig_cmi': fig_cmi.to_html(full_html=False, include_plotlyjs=False),
        'fig_peer': fig_peer.to_html(full_html=False, include_plotlyjs=False),
    }

    return render_template('hekim_puan.html',
        start_date=sd, end_date=ed, no_data=False,
        total_puan=total_puan, total_gelir=total_gelir,
        total_hasta=total_hasta, aktif_hekim=len(hekim_perf),
        avg_calisma_gun=avg_calisma_gun, genel_cmi_gelir=genel_cmi_gelir,
        hekimler=hekim_perf['Hekim'].tolist(),
        hekim_stats_dict=hekim_stats_dict,
        hekim_hizmet_dict=hekim_hizmet_dict,
        df_detayli_records=df_detayli_records,
        hekim_perf_records=hekim_perf_records,
        charts=charts, current_sort=sort_by, current_limit=limit,
        page_sql_kodlari=PAGE_SQL_KODLARI,
    )
