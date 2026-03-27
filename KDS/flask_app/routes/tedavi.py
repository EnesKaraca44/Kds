from flask import Blueprint, render_template, request
import pandas as pd
import plotly.express as px
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required
from database.tedavi_grubu_sorgular import tedavi_grubu_verisi_yukle
from routes.dashboard import get_date_range

tedavi_bp = Blueprint('tedavi', __name__)


@tedavi_bp.route('/tedavi')
@login_required
def tedavi():
    sd, ed = get_date_range()
    df_raw = tedavi_grubu_verisi_yukle(sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d'))

    if df_raw.empty:
        return render_template('tedavi.html', start_date=sd, end_date=ed, no_data=True, top_n=15)

    df = df_raw.copy()
    df.columns = [c.upper().strip() for c in df.columns]

    group_col, patient_col, revenue_col, count_col = 'TEDAVI_GRUBU_ADI', 'HASTA_KODU', 'TETKIK_TOPLAM_UCRET', 'TOPLAM_ADET'
    df = df[~df[group_col].isin(['BELİRTİLMEMİŞ', '', None])]

    summary = df.groupby(group_col, as_index=False).agg({
        patient_col: 'nunique',
        count_col: 'sum',
        revenue_col: 'sum',
    }).rename(
        columns={
            patient_col: 'HASTA_SAYISI',
            count_col: 'ISLEM_ADETI',
            revenue_col: 'TOPLAM_CIRO',
        }
    )

    try:
        top_n = int(request.args.get('top', 15))
    except (TypeError, ValueError):
        top_n = 15
    top_n = max(5, min(50, (top_n // 5) * 5))

    top_gelir = summary.nlargest(top_n, 'TOPLAM_CIRO').sort_values('TOPLAM_CIRO')
    fig_gelir = px.bar(
        top_gelir,
        x='TOPLAM_CIRO',
        y=group_col,
        orientation='h',
        color='TOPLAM_CIRO',
        color_continuous_scale='Blues',
        text_auto='.3s',
    )
    fig_gelir.update_traces(textposition='outside', cliponaxis=False)
    fig_gelir.update_layout(
        template='plotly_dark',
        height=480,
        margin=dict(l=10, r=40, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, tickformat='.3s', title=''),
        yaxis=dict(title='', tickfont=dict(size=10)),
        coloraxis_colorbar=dict(title='Ciro', tickformat='.2s'),
        showlegend=False,
    )

    top_islem = summary.nlargest(top_n, 'ISLEM_ADETI').sort_values('ISLEM_ADETI')
    fig_islem = px.bar(
        top_islem,
        x='ISLEM_ADETI',
        y=group_col,
        orientation='h',
        color='ISLEM_ADETI',
        color_continuous_scale='Greens',
        text_auto='.3s',
    )
    fig_islem.update_traces(textposition='outside', cliponaxis=False)
    fig_islem.update_layout(
        template='plotly_dark',
        height=480,
        margin=dict(l=10, r=40, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, tickformat='.3s', title=''),
        yaxis=dict(title='', tickfont=dict(size=10)),
        coloraxis_colorbar=dict(title='Adet', tickformat='.2s'),
        showlegend=False,
    )

    summary = summary[summary['ISLEM_ADETI'] > 0].copy()
    summary['ISLEM_BASI_GELIR'] = summary['TOPLAM_CIRO'] / summary['ISLEM_ADETI']
    
    # Verimlilik Analizi için outlierları engelleyerek en büyük ciro yapanları al
    scatter_df = summary.nlargest(top_n, 'TOPLAM_CIRO')
    
    # Plotly'de her kategoride tek bir satır veri olunca 'size' (büyüklük) matematiksel olarak 0 piksele düşüyor ve grafik boş çıkıyordu.
    # Y-Eksenine direkt Birim Başı Geliri (Verimlilik) koyarak analizi daha mantıklı hale getirdik.
    # Verilerimizi temiz ve güvenli bir şekilde döngüyle primitives (liste) haline getiriyoruz.
    # Pandas veya Numpy'deki olası NaN/bdata sorunları Plotly'de render hatası çıkarabiliyor.
    x_vals, y_vals, text_vals, ciro_vals = [], [], [], []
    
    for _, row in scatter_df.iterrows():
        adet = float(row['ISLEM_ADETI'])
        verim = float(row['ISLEM_BASI_GELIR'])
        ciro = float(row['TOPLAM_CIRO'])
        if pd.isna(adet) or pd.isna(verim) or pd.isna(ciro) or adet <= 0:
            continue
            
        x_vals.append(adet)
        y_vals.append(verim)
        ciro_vals.append(ciro)
        text_vals.append(str(row[group_col]))
        
    import plotly.graph_objects as go
    fig_scatter = go.Figure()

    if x_vals:
        fig_scatter.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode='markers+text',
            text=text_vals, # İsimler baloncukların üzerinde yazsın
            textposition='top center',
            marker=dict(
                size=18, # SABİT BOYUT: Ölçeklendirici crashe girmesin diye tüm yuvarlaklar aynı boyutta.
                color=y_vals, # Rengi verimliliğe göre yapıyoruz
                colorscale='Plasma',
                showscale=True,
                colorbar=dict(title='Verimlilik', thickness=15),
                line=dict(width=1.5, color='rgba(255,255,255,0.7)')
            ),
            customdata=ciro_vals,
            hovertemplate="<b>%{text}</b><br>Hacim: %{x:,.0f}<br>Verimlilik: ₺%{y:,.2f}<br>Ciro: ₺%{customdata:,.2f}<extra></extra>"
        ))
    
    fig_scatter.update_layout(
        template='plotly_dark',
        height=450,
        margin=dict(l=30, r=20, t=30, b=30),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(tickformat='.3s', title='İşlem Adeti (Hacim)', zeroline=True, showgrid=True, gridcolor='rgba(255,255,255,0.08)'),
        yaxis=dict(tickformat='.3s', title='Birim Başı Gelir', zeroline=True, showgrid=True, gridcolor='rgba(255,255,255,0.08)'),
    )

    insights = []
    try:
        sorted_rev = summary.sort_values('TOPLAM_CIRO', ascending=False)
        top3 = sorted_rev.head(3)
        for _, r in top3.iterrows():
            insights.append({
                "title": str(r[group_col]),
                "ciro": float(r['TOPLAM_CIRO']),
                "islem": int(r['ISLEM_ADETI']),
            })
        total = float(summary['TOPLAM_CIRO'].sum())
        if total > 0:
            pct = float(top3['TOPLAM_CIRO'].sum()) / total * 100.0
            insights.append({"share_pct": pct})
    except Exception:
        insights = []

    # Grup detayları için seçim ve tablo
    group_list = sorted(df[group_col].unique())
    selected_group = request.args.get('grup') or (group_list[0] if group_list else None)
    detay_rows = []
    if selected_group:
        g_df = df[df[group_col] == selected_group]
        detay = (
            g_df.groupby('TETKIK_ADI')
            .agg({count_col: 'sum', revenue_col: 'sum'})
            .sort_values(count_col, ascending=False)
            .reset_index()
        )
        for _, row in detay.iterrows():
            detay_rows.append(
                {
                    "tetkik_adi": row['TETKIK_ADI'],
                    "adet": int(row[count_col]),
                    "ciro": float(row[revenue_col]),
                }
            )

    charts = {
        'fig_gelir': fig_gelir.to_html(full_html=False, include_plotlyjs=False),
        'fig_islem': fig_islem.to_html(full_html=False, include_plotlyjs=False),
        'fig_scatter': fig_scatter.to_html(full_html=False, include_plotlyjs=False),
    }

    return render_template('tedavi.html',
        start_date=sd, end_date=ed, no_data=False,
        grup_sayisi=df[group_col].nunique(), tekil_hasta=df[patient_col].nunique(),
        islem_hacmi=df[count_col].sum(), toplam_ciro=df[revenue_col].sum(),
        charts=charts,
        top_n=top_n,
        insights=insights,
        group_list=group_list,
        selected_group=selected_group,
        detay_rows=detay_rows,
    )
