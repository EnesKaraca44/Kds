from flask import Blueprint, render_template
import pandas as pd
import plotly.express as px
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required
from flask_app.database.yabanci_hasta_sorgular import yabanci_hasta_verisi_yukle
from routes.dashboard import get_date_range

yabanci_hasta_bp = Blueprint('yabanci_hasta', __name__)


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


@yabanci_hasta_bp.route('/yabanci-hasta')
@login_required
def yabanci_hasta():
    sd, ed = get_date_range()
    df_raw = yabanci_hasta_verisi_yukle(sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d'))

    if df_raw.empty:
        return render_template('yabanci_hasta.html', start_date=sd, end_date=ed, no_data=True)

    df = df_raw.copy()
    df['Fiyat'] = pd.to_numeric(df['Fiyat'], errors='coerce').fillna(0)

    # YAS sütununu Plotly uyumlu float'a çevir
    if 'YAS' in df.columns:
        df['YAS'] = pd.to_numeric(df['YAS'], errors='coerce')
        df = df[df['YAS'].notna() & (df['YAS'] >= 0) & (df['YAS'] <= 120)].copy()

    # Cinsiyet temizliği
    if 'Cinsiyet' in df.columns:
        df['Cinsiyet'] = df['Cinsiyet'].fillna('Bilinmiyor').astype(str)

    import sys
    print(f"[YH] satir={len(df)} sutunlar={list(df.columns)}", flush=True, file=sys.stderr)

    total_patients = df['HastaAdi'].nunique()
    total_revenue = df['Fiyat'].sum()
    avg_rev = total_revenue / total_patients if total_patients > 0 else 0

    country_summary = (
        df.groupby('Ulke')
        .agg(Hasta_Sayisi=('HastaAdi', 'nunique'), Toplam_Gelir=('Fiyat', 'sum'))
        .reset_index()
    )
    country_summary['Hasta_Sayisi'] = country_summary['Hasta_Sayisi'].astype(float)
    country_summary['Toplam_Gelir'] = country_summary['Toplam_Gelir'].astype(float)
    country_summary['Hasta_Basi_Gelir'] = country_summary.apply(
        lambda r: r['Toplam_Gelir'] / r['Hasta_Sayisi'] if r['Hasta_Sayisi'] > 0 else 0, axis=1
    ).astype(float)
    eff_table = []
    max_country_revenue = max(_safe_float(country_summary['Toplam_Gelir'].max()), 1.0) if not country_summary.empty else 1.0
    for row in (
        country_summary
        .sort_values(['Hasta_Basi_Gelir', 'Toplam_Gelir'], ascending=[False, False])
        .head(30)
        .to_dict(orient='records')
    ):
        gelir = _safe_float(row['Toplam_Gelir'])
        hasta_basi = _safe_float(row['Hasta_Basi_Gelir'])
        if hasta_basi >= 10000:
            yorum = 'Yuksek deger'
            seviye = 'high'
        elif hasta_basi >= 4000:
            yorum = 'Dengeli'
            seviye = 'medium'
        else:
            yorum = 'Hacim odakli'
            seviye = 'low'
        eff_table.append({
            'ulke': row['Ulke'],
            'hasta_sayisi': int(_safe_float(row['Hasta_Sayisi'])),
            'toplam_gelir': gelir,
            'hasta_basi_gelir': round(hasta_basi, 2),
            'bar_width': max(6, min(int((gelir / max_country_revenue) * 100), 100)),
            'seviye': seviye,
            'yorum': yorum,
        })

    # Coğrafi dağılım
    top_geo_rev = country_summary.nlargest(10, 'Toplam_Gelir').sort_values('Toplam_Gelir')
    fig_geo_bar = px.bar(
        top_geo_rev,
        x='Toplam_Gelir',
        y='Ulke',
        orientation='h',
        color='Toplam_Gelir',
        color_continuous_scale='Plasma',
    )
    fig_geo_bar.update_traces(texttemplate='%{x:.3s}', textposition='outside', cliponaxis=False)
    fig_geo_bar.update_layout(
        template='plotly_dark',
        height=420,
        margin=dict(l=10, r=60, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, tickformat='.3s', title=''),
        yaxis=dict(title='', tickfont=dict(size=10)),
        coloraxis_colorbar=dict(title='Gelir', tickformat='.2s'),
        showlegend=False,
    )

    top_geo_pat = country_summary.nlargest(10, 'Hasta_Sayisi')
    fig_geo_pie = px.pie(
        top_geo_pat,
        values='Hasta_Sayisi',
        names='Ulke',
        hole=0.45,
    )
    fig_geo_pie.update_traces(textinfo='percent+label')
    fig_geo_pie.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(l=20, r=20, t=10, b=10),
    )

    # Verimlilik matrisi
    scatter_data = country_summary[country_summary['Hasta_Basi_Gelir'] > 0].copy()
    print(f"[YH] scatter_data satir={len(scatter_data)}", flush=True, file=sys.stderr)

    if not scatter_data.empty:
        fig_eff = px.scatter(
            scatter_data,
            x='Hasta_Sayisi',
            y='Toplam_Gelir',
            size='Hasta_Basi_Gelir',
            color='Ulke',
            hover_name='Ulke',
            labels={'Hasta_Sayisi': 'Hasta Sayısı', 'Toplam_Gelir': 'Toplam Gelir (₺)'},
        )
    else:
        fig_eff = px.scatter(
            country_summary,
            x='Hasta_Sayisi',
            y='Toplam_Gelir',
            color='Ulke',
            hover_name='Ulke',
            labels={'Hasta_Sayisi': 'Hasta Sayısı', 'Toplam_Gelir': 'Toplam Gelir (₺)'},
        )
    fig_eff.update_layout(
        template='plotly_dark',
        height=420,
        margin=dict(l=10, r=10, t=30, b=30),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(tickformat='.3s', title='Hasta Sayısı'),
        yaxis=dict(tickformat='.3s', title='Toplam Gelir (₺)'),
        legend=dict(
            x=1.01,
            y=1,
            bgcolor='rgba(13,27,62,0.85)',
            bordercolor='#2d4a8a',
            borderwidth=1,
            font=dict(size=9),
        ),
    )

    # Demografi
    has_yas = 'YAS' in df.columns and df['YAS'].notna().sum() > 0
    has_cinsiyet = 'Cinsiyet' in df.columns and df['Cinsiyet'].notna().sum() > 0
    print(f"[YH] has_yas={has_yas} has_cinsiyet={has_cinsiyet}", flush=True, file=sys.stderr)

    if has_yas:
        demo_df = df[df['YAS'].notna()].copy()
        demo_df['YAS'] = demo_df['YAS'].astype(float)
        fig_demo_hist = px.histogram(
            demo_df,
            x='YAS',
            color='Cinsiyet' if has_cinsiyet else None,
            barmode='group',
            nbins=30,
            labels={'YAS': 'Yaş', 'count': 'Hasta Sayısı'},
        )
    else:
        fig_demo_hist = px.bar(title='Yaş verisi bulunamadı')

    fig_demo_hist.update_layout(
        template='plotly_dark',
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=30, r=10, t=30, b=30),
        xaxis_title='Yaş',
        yaxis_title='Hasta Sayısı',
    )

    if has_cinsiyet:
        gender_counts = df['Cinsiyet'].value_counts().reset_index()
        gender_counts.columns = ['Cinsiyet', 'Sayi']
        gender_counts['Sayi'] = gender_counts['Sayi'].astype(float)
        fig_demo_pie = px.pie(
            gender_counts,
            values='Sayi',
            names='Cinsiyet',
            hole=0.45,
        )
    else:
        fig_demo_pie = px.pie(title='Cinsiyet verisi bulunamadı')

    fig_demo_pie.update_layout(
        template='plotly_dark',
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        margin=dict(l=20, r=20, t=30, b=10),
    )
    demo_table = []
    if has_yas:
        demo_source = df.copy()
        if 'Cinsiyet' not in demo_source.columns:
            demo_source['Cinsiyet'] = 'Bilinmiyor'
        demo_source['YAS_GRUBU'] = pd.cut(
            demo_source['YAS'],
            bins=[0, 17, 25, 35, 45, 55, 65, 120],
            labels=['0-17', '18-25', '26-35', '36-45', '46-55', '56-65', '66+'],
            include_lowest=True,
        )
        demo_summary = (
            demo_source.groupby(['YAS_GRUBU', 'Cinsiyet'])['HastaAdi']
            .nunique()
            .reset_index(name='Hasta_Sayisi')
        )
        if not demo_summary.empty:
            pivot_demo = (
                demo_summary.pivot(index='YAS_GRUBU', columns='Cinsiyet', values='Hasta_Sayisi')
                .fillna(0)
                .sort_index()
            )
            gender_cols = list(pivot_demo.columns)
            max_demo_total = max(_safe_float(pivot_demo.sum(axis=1).max()), 1.0)
            for age_group, row in pivot_demo.iterrows():
                toplam = int(_safe_float(row.sum()))
                cinsiyetler = []
                for gender in gender_cols:
                    value = int(_safe_float(row[gender]))
                    cinsiyetler.append({'ad': str(gender), 'sayi': value})
                demo_table.append({
                    'yas_grubu': str(age_group),
                    'toplam': toplam,
                    'bar_width': max(6, min(int((toplam / max_demo_total) * 100), 100)),
                    'cinsiyetler': cinsiyetler,
                })

    charts = {
        'fig_geo_bar': fig_geo_bar.to_html(full_html=False, include_plotlyjs=False),
        'fig_geo_pie': fig_geo_pie.to_html(full_html=False, include_plotlyjs=False),
        'fig_eff': fig_eff.to_html(full_html=False, include_plotlyjs=False),
        'fig_demo_hist': fig_demo_hist.to_html(full_html=False, include_plotlyjs=False),
        'fig_demo_pie': fig_demo_pie.to_html(full_html=False, include_plotlyjs=False),
    }

    insights = []
    if not country_summary.empty:
        top3 = country_summary.sort_values('Toplam_Gelir', ascending=False).head(3)
        total_gelir = float(country_summary['Toplam_Gelir'].sum())
        for _, row in top3.iterrows():
            insights.append(
                {
                    "ulke": str(row['Ulke']),
                    "gelir": float(row['Toplam_Gelir']),
                    "hasta": int(row['Hasta_Sayisi']),
                }
            )
        if total_gelir > 0:
            pay = float(top3['Toplam_Gelir'].sum()) / total_gelir * 100.0
            insights.append({"share_pct": pay})

    return render_template('yabanci_hasta.html',
        start_date=sd, end_date=ed, no_data=False,
        total_patients=total_patients, total_revenue=total_revenue,
        avg_rev=avg_rev, ulke_cesitlilik=df['Ulke'].nunique(),
        charts=charts,
        eff_table=eff_table,
        demo_table=demo_table,
        insights=insights,
    )
