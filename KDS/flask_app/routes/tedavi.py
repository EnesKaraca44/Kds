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
    scatter_df = summary.nlargest(top_n, 'ISLEM_BASI_GELIR')
    fig_scatter = px.scatter(
        scatter_df,
        x='ISLEM_ADETI',
        y='TOPLAM_CIRO',
        size='ISLEM_BASI_GELIR',
        color=group_col,
        hover_name=group_col,
    )
    fig_scatter.update_layout(
        template='plotly_dark',
        height=420,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(tickformat='.3s', title=''),
        yaxis=dict(tickformat='.3s', title=''),
        legend=dict(
            x=1.01,
            y=1,
            bgcolor='rgba(13,27,62,0.8)',
            bordercolor='#2d4a8a',
            borderwidth=1,
            font=dict(size=10),
        ),
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
