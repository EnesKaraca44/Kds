from flask import Blueprint, render_template, request
import pandas as pd
import plotly.express as px
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required
from database.randevu_sorgular import randevu_verisi_yukle
from routes.dashboard import get_date_range

randevu_bp = Blueprint('randevu', __name__)


@randevu_bp.route('/randevu')
@login_required
def randevu():
    sd, ed = get_date_range()
    df_raw = randevu_verisi_yukle(sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d'))

    if df_raw.empty:
        return render_template('randevu.html', start_date=sd, end_date=ed, no_data=True, top_n=15)

    df = df_raw.copy()
    df['Trh'] = pd.to_datetime(df['Trh'], errors='coerce')

    # KPI hesaplamaları
    status_counts = df['Durum'].value_counts()
    hizmet_alan = int(status_counts.get('Geldi', 0) + status_counts.get('Geç Geldi', 0))
    toplam = len(df)
    sadakat_orani = round((hizmet_alan / toplam * 100), 1) if toplam > 0 else 0
    kayip_orani = round(100 - sadakat_orani, 1)
    aktif_hekim = df[df['dktad'] != 'BELİRTİLMEMİŞ']['dktad'].nunique()

    try:
        top_n = int(request.args.get('top', 15))
    except (TypeError, ValueError):
        top_n = 15
    top_n = max(5, min(50, (top_n // 5) * 5))

    # ── Tab 1: Hekim Performansı ─────────────────────────────────────────────
    doc_sum = df[df['dktad'] != 'BELİRTİLMEMİŞ'].groupby('dktad').agg(
        Toplam=('RandevuID', 'size'),
        Hizmet=('Durum', lambda x: x.isin(['Geldi', 'Geç Geldi']).sum()),
    ).reset_index()
    doc_sum['Sadakat_Orani'] = (doc_sum['Hizmet'] / doc_sum['Toplam'] * 100).round(1)

    top_sadakat = doc_sum.nlargest(top_n, 'Sadakat_Orani').sort_values('Sadakat_Orani')
    fig_sadakat = px.bar(
        top_sadakat,
        x='Sadakat_Orani',
        y='dktad',
        orientation='h',
        color='Sadakat_Orani',
        color_continuous_scale='YlGn',
        labels={'Sadakat_Orani': 'Sadakat Oranı', 'dktad': ''},
    )
    fig_sadakat.update_traces(
        texttemplate='%{x:.1f}%',
        textposition='outside',
        cliponaxis=False,
    )
    fig_sadakat.update_layout(
        template='plotly_dark',
        height=500,
        margin=dict(l=10, r=50, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, title='Sadakat Oranı', range=[0, 105]),
        yaxis=dict(title='', tickfont=dict(size=10)),
        coloraxis_colorbar=dict(title='Sadakat_Orani', tickformat='.0f'),
        showlegend=False,
    )

    # ── Tab 2: Kanal & Poliklinik ────────────────────────────────────────────
    pol_counts = df['SrvAd'].value_counts().nlargest(10).reset_index()
    pol_counts.columns = ['SrvAd', 'Sayi']
    fig_pol = px.pie(
        pol_counts,
        values='Sayi',
        names='SrvAd',
        hole=0.45,
    )
    fig_pol.update_traces(textinfo='percent+label', textposition='outside')
    fig_pol.update_layout(
        template='plotly_dark',
        height=420,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(
            x=1.01, y=1,
            bgcolor='rgba(13,27,62,0.85)',
            bordercolor='#2d4a8a',
            borderwidth=1,
            font=dict(size=9),
        ),
        margin=dict(l=20, r=180, t=10, b=10),
    )

    kanal_counts = df['Randevuverilme_Yeri'].value_counts().reset_index()
    kanal_counts.columns = ['Kanal', 'Sayi']
    fig_kanal = px.bar(
        kanal_counts.sort_values('Sayi'),
        x='Sayi',
        y='Kanal',
        orientation='h',
        color_discrete_sequence=['#6366f1'],
        labels={'Sayi': 'Randevu Sayısı', 'Kanal': ''},
    )
    fig_kanal.update_traces(texttemplate='%{x:.3s}', textposition='outside', cliponaxis=False)
    fig_kanal.update_layout(
        template='plotly_dark',
        height=420,
        margin=dict(l=10, r=50, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, title=''),
        yaxis=dict(title='', tickfont=dict(size=10)),
        showlegend=False,
    )

    # ── Tab 3: Akıllı Yorumlar ───────────────────────────────────────────────
    insights = []
    insights.append({
        'type': 'success',
        'icon': '✅',
        'text': f"Kurum genelinde randevuların <strong>%{sadakat_orani}</strong> kadarı hizmete dönüşüyor.",
    })

    if sadakat_orani < 70:
        insights.append({
            'type': 'info',
            'icon': '📋',
            'text': "Öneri: Sadakat oranı %70'in altında kalan hekimler için SMS onay sistemi zorunlu hale getirilebilir.",
        })
    else:
        insights.append({
            'type': 'info',
            'icon': '📋',
            'text': "Öneri: Sadakat oranı %70'in altında kalan hekimler için SMS onay sistemi zorunlu hale getirilebilir.",
        })

    if not df.empty:
        gelmedi_df = df[df['Durum'].isin(['Gelmedi'])]
        if not gelmedi_df.empty:
            worst_pol = gelmedi_df['SrvAd'].value_counts().idxmax()
            insights.append({
                'type': 'warning',
                'icon': '⚠️',
                'text': f"En fazla randevu kaybı (No show) <strong>{worst_pol}</strong> polikliniğinde.",
            })

    charts = {
        'fig_sadakat': fig_sadakat.to_html(full_html=False, include_plotlyjs=False),
        'fig_pol': fig_pol.to_html(full_html=False, include_plotlyjs=False),
        'fig_kanal': fig_kanal.to_html(full_html=False, include_plotlyjs=False),
    }

    return render_template('randevu.html',
        start_date=sd, end_date=ed, no_data=False,
        toplam_randevu=toplam,
        sadakat_orani=sadakat_orani,
        kayip_orani=kayip_orani,
        hizmet_alan=hizmet_alan,
        aktif_hekim=aktif_hekim,
        charts=charts,
        top_n=top_n,
        insights=insights,
    )
