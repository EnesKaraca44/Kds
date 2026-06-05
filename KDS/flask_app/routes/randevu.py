from flask import Blueprint, render_template, request
import pandas as pd
import plotly.express as px
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required
from database.randevu_sorgular import randevu_verisi_yukle
from routes.dashboard import get_date_range

randevu_bp = Blueprint('randevu', __name__)

PAGE_SQL_KODLARI = ["randevu.randevu_verisi_yukle"]

_SKIP_SRV = frozenset({'', 'BELİRTİLMEMİŞ', 'BELIRTILMEMIS', 'NAN', 'NONE', 'NULL'})

_INSIGHT_TR = {
    'INSIGHT_APPOINTMENT_SUCCESS': (
        'Kurum genelinde randevuların <strong>%{0}</strong> kadarı hizmete dönüşüyor.'
    ),
    'INSIGHT_APPOINTMENT_SUGGESTION': (
        'Öneri: Sadakat oranı %70\'in altında kalan hekimler için SMS onay sistemi '
        'zorunlu hale getirilebilir.'
    ),
    'INSIGHT_APPOINTMENT_WORST_POL': (
        'En fazla randevu kaybı (No show) <strong>{0}</strong> polikliniğinde.'
    ),
}


def _insight_html(payload):
    """INSIGHT_KEY veya INSIGHT_KEY|param -> Turkce HTML."""
    if not payload:
        return ''
    if '|' in payload:
        key, *values = payload.split('|')
        template = _INSIGHT_TR.get(key, payload)
        for index, value in enumerate(values):
            template = template.replace(f'{{{index}}}', str(value))
            template = template.replace(f'%{{{index}}}', str(value))
        return template
    return _INSIGHT_TR.get(payload, payload)


def _find_column(df, candidates):
    normalized = {str(col).strip().lower(): col for col in df.columns}
    for candidate in candidates:
        key = str(candidate).strip().lower()
        if key in normalized:
            return normalized[key]
    return None


def _normalize_randevu_df(df_raw):
    """ODBC / API sutun adlarini tek forma getir."""
    df = df_raw.copy()
    mappings = (
        ('SrvAd', ('SrvAd', 'SRVAD', 'BIRIM_AD', 'birim_ad', 'SevkEdilenKlinik')),
        ('RandevuID', ('RandevuID', 'RANDEVUID', 'SEVK_ID', 'sevk_id')),
        ('Durum', ('Durum', 'DURUM')),
        ('dktad', ('dktad', 'DKTAD', 'DOKTOR_AD', 'HekimAdi')),
        ('Randevuverilme_Yeri', ('Randevuverilme_Yeri', 'RANDEVU_TURU_ADI', 'randevu_turu_adi')),
    )
    for target, candidates in mappings:
        source = _find_column(df, candidates)
        if source:
            df[target] = df[source]
    if 'SrvAd' in df.columns:
        df['SrvAd'] = df['SrvAd'].fillna('').astype(str).str.strip()
    if 'RandevuID' in df.columns:
        df['RandevuID'] = df['RandevuID'].astype(str)
    return df


def _poliklinik_sayim(df, limit=10):
    """Benzersiz randevu sayisina gore en yogun poliklinikler."""
    if 'SrvAd' not in df.columns or 'RandevuID' not in df.columns:
        return pd.DataFrame(columns=['SrvAd', 'Sayi', 'Yuzde', 'Bar_Label'])

    mask = ~df['SrvAd'].str.upper().isin(_SKIP_SRV)
    work = df.loc[mask]
    if work.empty:
        return pd.DataFrame(columns=['SrvAd', 'Sayi', 'Yuzde', 'Bar_Label'])

    pol = (
        work.groupby('SrvAd', as_index=False)
        .agg(Sayi=('RandevuID', 'nunique'))
    )
    pol = pol.nlargest(limit, 'Sayi')
    total = float(pol['Sayi'].sum())
    if total <= 0:
        pol['Yuzde'] = 0.0
    else:
        pol['Yuzde'] = (pol['Sayi'] / total * 100).round(1)
    pol['Bar_Label'] = pol.apply(
        lambda r: f"{int(r['Sayi'])} (%{r['Yuzde']:.1f})",
        axis=1,
    )
    return pol.sort_values('Sayi')


@randevu_bp.route('/randevu')
@login_required
def randevu():
    sd, ed = get_date_range()
    df_raw = randevu_verisi_yukle(sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d'))

    if df_raw.empty:
        return render_template('randevu.html', start_date=sd, end_date=ed, no_data=True, top_n=15, page_sql_kodlari=PAGE_SQL_KODLARI)

    df = _normalize_randevu_df(df_raw)
    if 'Trh' in df.columns:
        df['Trh'] = pd.to_datetime(df['Trh'], errors='coerce')

    # KPI hesaplamaları (benzersiz randevu)
    toplam = int(df['RandevuID'].nunique()) if 'RandevuID' in df.columns else len(df)
    if 'Durum' in df.columns and 'RandevuID' in df.columns:
        hizmet_alan = int(
            df[df['Durum'].isin(['Geldi', 'Geç Geldi'])]['RandevuID'].nunique()
        )
    else:
        status_counts = df['Durum'].value_counts() if 'Durum' in df.columns else pd.Series(dtype=int)
        hizmet_alan = int(status_counts.get('Geldi', 0) + status_counts.get('Geç Geldi', 0))
    sadakat_orani = round((hizmet_alan / toplam * 100), 1) if toplam > 0 else 0
    kayip_orani = round(100 - sadakat_orani, 1)
    aktif_hekim = df[df['dktad'] != 'BELİRTİLMEMİŞ']['dktad'].nunique()

    try:
        top_n = int(request.args.get('top', 15))
    except (TypeError, ValueError):
        top_n = 15
    top_n = max(5, min(50, (top_n // 5) * 5))

    # ── Tab 1: Hekim Performansı ─────────────────────────────────────────────
    hekim_df = df[df['dktad'].fillna('').astype(str).str.upper() != 'BELİRTİLMEMİŞ'].copy()
    doc_sum = hekim_df.groupby('dktad', as_index=False).agg(Toplam=('RandevuID', 'nunique'))
    geldi_per_hekim = (
        hekim_df[hekim_df['Durum'].isin(['Geldi', 'Geç Geldi'])]
        .groupby('dktad', as_index=False)
        .agg(Hizmet=('RandevuID', 'nunique'))
    )
    doc_sum = doc_sum.merge(geldi_per_hekim, on='dktad', how='left')
    doc_sum['Hizmet'] = doc_sum['Hizmet'].fillna(0).astype(int)
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
        coloraxis_colorbar=dict(title='Sadakat Oranı', tickformat='.0f'),
        showlegend=False,
    )

    # ── Tab 2: Kanal & Poliklinik ────────────────────────────────────────────
    pol_counts = _poliklinik_sayim(df, limit=10)
    if pol_counts.empty:
        fig_pol = px.bar(title='Poliklinik verisi bulunamadı')
        fig_pol.update_layout(
            template='plotly_dark',
            height=460,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )
    else:
        fig_pol = px.bar(
            pol_counts,
            x='Sayi',
            y='SrvAd',
            orientation='h',
            text='Bar_Label',
            color_discrete_sequence=['#0ea5e9'],
            labels={'Sayi': 'Randevu Sayısı', 'SrvAd': ''},
        )
        fig_pol.update_traces(
            texttemplate='%{text}',
            textposition='outside',
            cliponaxis=False,
            hovertemplate=(
                '<b>%{y}</b><br>'
                'Randevu: %{x:,}<br>'
                'Pay: %{customdata}<extra></extra>'
            ),
            customdata=pol_counts['Yuzde'].apply(lambda v: f'%{v:.1f}'),
        )
        fig_pol.update_layout(
            template='plotly_dark',
            height=460,
            margin=dict(l=10, r=90, t=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(148, 163, 184, 0.18)',
                title='Randevu Sayısı',
                tickformat=',.0f',
            ),
            yaxis=dict(title='', tickfont=dict(size=10), automargin=True),
            showlegend=False,
        )

    kanal_col = 'Randevuverilme_Yeri' if 'Randevuverilme_Yeri' in df.columns else None
    if kanal_col and 'RandevuID' in df.columns:
        kanal_counts = (
            df[df[kanal_col].fillna('').astype(str).str.strip().astype(bool)]
            .groupby(kanal_col, as_index=False)
            .agg(Sayi=('RandevuID', 'nunique'))
            .sort_values('Sayi')
        )
        kanal_counts.columns = ['Kanal', 'Sayi']
    else:
        kanal_counts = pd.DataFrame(columns=['Kanal', 'Sayi'])
    fig_kanal = px.bar(
        kanal_counts,
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
    success_key = f"INSIGHT_APPOINTMENT_SUCCESS|{sadakat_orani}"
    insights.append({
        'type': 'success',
        'icon': '✅',
        'text': _insight_html(success_key),
        'data_t': success_key,
    })

    suggestion_key = 'INSIGHT_APPOINTMENT_SUGGESTION'
    insights.append({
        'type': 'info',
        'icon': '📋',
        'text': _insight_html(suggestion_key),
        'data_t': suggestion_key,
    })

    if not df.empty:
        gelmedi_df = df[df['Durum'].isin(['Gelmedi'])]
        if not gelmedi_df.empty:
            worst_pol = gelmedi_df['SrvAd'].value_counts().idxmax()
            worst_key = f"INSIGHT_APPOINTMENT_WORST_POL|{worst_pol}"
            insights.append({
                'type': 'warning',
                'icon': '⚠️',
                'text': _insight_html(worst_key),
                'data_t': worst_key,
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
        page_sql_kodlari=PAGE_SQL_KODLARI,
    )
