from flask import Blueprint, render_template, request
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required
from database.malzeme_sorgular import (
    malzeme_tuketim_verisi_yukle,
    depo_mevcut_verisi_yukle,
    depo_birim_liste_yukle,
)
from routes.dashboard import get_date_range

malzeme_bp = Blueprint('malzeme', __name__)


@malzeme_bp.route('/malzeme')
@login_required
def malzeme():
    sd, ed = get_date_range()
    df_raw = malzeme_tuketim_verisi_yukle(sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d'))
    depo_liste_df = depo_birim_liste_yukle()
    depo_options = []
    if depo_liste_df is not None and not depo_liste_df.empty:
        for row in depo_liste_df.to_dict(orient='records'):
            birim_id = row.get('birimId')
            if pd.isna(birim_id):
                continue
            depo_id = str(int(float(birim_id)))
            depo_options.append({
                'id': depo_id,
                'ad': str(row.get('birimAd') or f"Birim {depo_id}"),
            })

    valid_depo_ids = {opt['id'] for opt in depo_options}
    selected_depo = (request.args.get('depo', default='', type=str) or '').strip()
    if selected_depo not in valid_depo_ids:
        selected_depo = ''

    all_depo_ids = [opt['id'] for opt in depo_options]
    depo_df = depo_mevcut_verisi_yukle(
        sd.strftime('%Y-%m-%d'),
        ed.strftime('%Y-%m-%d'),
        birim_id=selected_depo or None,
        birim_id_list=all_depo_ids if not selected_depo and all_depo_ids else None
    )
    # "Tum Depolar" modunda, sadece combobox'ta listelenen depolari say.
    # Boylece toplam sayi, kullanicinin tek tek secebildigi depolarla tutarli olur.
    if not selected_depo and depo_df is not None and not depo_df.empty and depo_options:
        allowed_depo_names = {str(opt['ad']).strip() for opt in depo_options if opt.get('ad')}
        if allowed_depo_names and 'birimAd' in depo_df.columns:
            depo_df = depo_df[
                depo_df['birimAd'].fillna('').astype(str).str.strip().isin(allowed_depo_names)
            ].copy()
    active_kategori = request.args.get('kategori', default='7', type=str)
    if active_kategori not in {'1', '2', '3', '4', '5', '6', '7'}:
        active_kategori = '7'

    df = df_raw.copy() if df_raw is not None else pd.DataFrame()
    if not df.empty and 'dusumTarih' in df.columns:
        df['dusumTarih'] = pd.to_datetime(df['dusumTarih']).dt.date
    if 'toplam' in df.columns:
        df['toplam'] = pd.to_numeric(df['toplam'], errors='coerce').fillna(0).round(2)
    else:
        df['toplam'] = 0.0
    # Keep source precision; rounding before grouping can make totals look too low.
    if 'dusumMiktar' in df.columns:
        df['dusumMiktar'] = pd.to_numeric(df['dusumMiktar'], errors='coerce').fillna(0)
    else:
        df['dusumMiktar'] = 0.0
    if 'hastaAdSoyad' not in df.columns:
        df['hastaAdSoyad'] = ''
    if 'stokAd' not in df.columns:
        df['stokAd'] = ''
    if 'bransAdi' not in df.columns:
        df['bransAdi'] = ''
    if 'doktorAdSoyad' not in df.columns:
        df['doktorAdSoyad'] = ''
    if 'tetkikAdi' not in df.columns:
        df['tetkikAdi'] = ''

    no_data_1_5 = bool(df.empty)
    no_data_6_7 = bool(depo_df is None or depo_df.empty)
    no_data = no_data_1_5 and no_data_6_7
    no_data_6_7_message = (
        'Seçilen depo ve tarih aralığında kayıt bulunamadı.'
        if selected_depo else
        'Seçilen tarih aralığında depo kaydı bulunamadı.'
    )

    if df.empty or 'dusumTarih' not in df.columns:
        daily = pd.DataFrame(columns=['dusumTarih', 'dusumMiktar'])
        daily['5_Gunluk_Ort'] = pd.Series(dtype='float64')
    else:
        daily = df.groupby('dusumTarih')['dusumMiktar'].sum().reset_index().sort_values('dusumTarih')
        daily['5_Gunluk_Ort'] = daily['dusumMiktar'].rolling(window=5, min_periods=1).mean().round(1)

    # Trend (ilk tasarimdaki sade dikey gorunum)
    fig_trend = go.Figure()
    fig_trend.add_trace(
        go.Bar(
            x=daily['dusumTarih'],
            y=daily['dusumMiktar'],
            name='Günlük Tüketim',
            marker_color='#3498db',
        )
    )
    fig_trend.add_trace(
        go.Scatter(
            x=daily['dusumTarih'],
            y=daily['5_Gunluk_Ort'],
            name='5 Günlük Ort.',
            mode='lines',
            line=dict(color='#e74c3c', width=3, dash='dot'),
        )
    )
    fig_trend.update_layout(
        xaxis_title="Tarih",
        yaxis_title="Adet",
        template='plotly_white',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    # Kategori 3: Brans ve brans ici hekim analizi
    branch_df = df.copy()
    branch_df['bransAdi'] = branch_df['bransAdi'].fillna('').astype(str).str.strip()
    branch_df.loc[branch_df['bransAdi'] == '', 'bransAdi'] = 'BILINMEYEN BRANS'
    branch_df['doktorAdSoyad'] = branch_df['doktorAdSoyad'].fillna('').astype(str).str.strip()
    branch_df.loc[branch_df['doktorAdSoyad'] == '', 'doktorAdSoyad'] = 'BILINMEYEN HEKIM'
    branch_df['kayitAdet'] = 1
    branch_df['toplam'] = pd.to_numeric(branch_df['toplam'], errors='coerce').fillna(0.0)
    branch_df['dusumMiktar'] = pd.to_numeric(branch_df['dusumMiktar'], errors='coerce').fillna(0.0)

    # Pick metric by actual usable max value, not only total sum.
    metric_priority = ['toplam', 'dusumMiktar', 'kayitAdet']
    branch_metric_col = 'kayitAdet'
    for candidate in metric_priority:
        candidate_max = float(branch_df[candidate].max()) if not branch_df.empty else 0.0
        if candidate_max > 0:
            branch_metric_col = candidate
            break

    branch_sum = (
        branch_df.groupby('bransAdi', dropna=False)[branch_metric_col]
        .sum()
        .reset_index()
        .sort_values(branch_metric_col, ascending=False)
    )
    if float(branch_sum[branch_metric_col].max()) <= 0 and branch_metric_col != 'kayitAdet':
        branch_metric_col = 'kayitAdet'
        branch_sum = (
            branch_df.groupby('bransAdi', dropna=False)[branch_metric_col]
            .sum()
            .reset_index()
            .sort_values(branch_metric_col, ascending=False)
        )
    top10_branch = branch_sum.head(10)
    x_values = pd.to_numeric(top10_branch[branch_metric_col], errors='coerce').fillna(0).tolist()
    y_values = top10_branch['bransAdi'].astype(str).tolist()
    fig_branch_rank = go.Figure()
    fig_branch_rank.add_trace(
        go.Bar(
            x=x_values,
            y=y_values,
            orientation='h',
            marker=dict(color='#ef4444'),
            text=[f"{v:,.0f}".replace(",", ".") for v in x_values],
            textposition='outside',
            cliponaxis=False,
            name='Brans',
        )
    )
    fig_branch_rank.update_layout(
        title='En Cok Tuketen 10 Brans',
        yaxis_title='bransAdi',
        xaxis_title='Toplam Tutar' if branch_metric_col == 'toplam' else ('Tuketim Miktari' if branch_metric_col == 'dusumMiktar' else 'Kayit Adedi'),
        yaxis=dict(categoryorder='total ascending'),
        template='plotly_white',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=80, r=40, t=60, b=40),
    )

    brans_options = branch_sum['bransAdi'].tolist()
    selected_brans = request.args.get('brans', type=str) or (brans_options[0] if brans_options else None)
    if selected_brans not in brans_options and brans_options:
        selected_brans = brans_options[0]

    brans_df = branch_df[branch_df['bransAdi'] == selected_brans].copy() if selected_brans else pd.DataFrame()
    hekim_payi = pd.DataFrame(columns=['doktorAdSoyad', branch_metric_col])
    if not brans_df.empty:
        hekim_payi = (
            brans_df.groupby('doktorAdSoyad', dropna=False)[branch_metric_col]
            .sum()
            .reset_index()
            .sort_values(branch_metric_col, ascending=False)
            .head(10)
        )

    if hekim_payi.empty:
        fig_branch_doc_pie = go.Figure()
        fig_branch_doc_pie.add_annotation(
            text='Secilen tarih araliginda hekim verisi bulunamadi.',
            x=0.5, y=0.5, xref='paper', yref='paper', showarrow=False
        )
    else:
        fig_branch_doc_pie = px.pie(
            hekim_payi,
            values=branch_metric_col,
            names='doktorAdSoyad',
            title=f'{selected_brans or "Brans"} Hekim Paylari',
            hole=0.55,
        )
    fig_branch_doc_pie.update_layout(
        template='plotly_white',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    brans_debug = {
        'brans_sayisi': int(len(branch_sum)),
        'secili_brans_kayit': int(len(brans_df)),
        'tekil_hekim': int(hekim_payi['doktorAdSoyad'].nunique()) if not hekim_payi.empty else 0,
        'kullanim_metrigi': 'Toplam Tutar' if branch_metric_col == 'toplam' else ('Tuketim Miktari' if branch_metric_col == 'dusumMiktar' else 'Kayit Adedi'),
        'maks_deger': float(branch_sum[branch_metric_col].max()) if not branch_sum.empty else 0.0,
    }

    # Kategori 4: Maliyet & hasta iliskisi (balon: hasta basi maliyet)
    scatter_df = df.copy()
    scatter_df['doktorAdSoyad'] = scatter_df['doktorAdSoyad'].fillna('').astype(str).str.strip()
    scatter_df.loc[scatter_df['doktorAdSoyad'] == '', 'doktorAdSoyad'] = 'BILINMEYEN HEKIM'

    # If patient name is empty, create row-based fallback id so counts do not collapse to zero.
    scatter_df['hasta_key'] = scatter_df['hastaAdSoyad'].fillna('').astype(str).str.strip()
    scatter_df.loc[scatter_df['hasta_key'] == '', 'hasta_key'] = (
        'KAYIT_' + scatter_df.index.astype(str)
    )

    doc_perf = (
        scatter_df.groupby('doktorAdSoyad', dropna=False)
        .agg(
            hasta_sayisi=('hasta_key', 'nunique'),
            kayit_sayisi=('hasta_key', 'size'),
            toplam=('toplam', 'sum'),
        )
        .reset_index()
    )
    doc_perf['hasta_sayisi'] = doc_perf['hasta_sayisi'].where(doc_perf['hasta_sayisi'] > 0, doc_perf['kayit_sayisi']).fillna(1).astype(float)
    doc_perf['hasta_basi_maliyet'] = (doc_perf['toplam'] / doc_perf['hasta_sayisi']).fillna(0).round(2)
    doc_perf['balon_boyutu'] = doc_perf['hasta_basi_maliyet'].clip(lower=1)
    doc_perf = doc_perf.sort_values('toplam', ascending=False).head(30)

    doc_perf = doc_perf[
        doc_perf['hasta_sayisi'].notna()
        & doc_perf['toplam'].notna()
        & doc_perf['balon_boyutu'].notna()
    ].copy()
    doc_perf = doc_perf[(doc_perf['hasta_sayisi'] > 0) & (doc_perf['toplam'] >= 0) & (doc_perf['balon_boyutu'] > 0)]

    if len(doc_perf) == 1:
        r = doc_perf.iloc[0]
        fig_cost_patient = go.Figure()
        fig_cost_patient.add_trace(
            go.Scatter(
                x=[float(r['hasta_sayisi'])],
                y=[float(r['toplam'])],
                mode='markers+text',
                text=[str(r['doktorAdSoyad'])],
                textposition='top center',
                marker=dict(size=30, color='#1f77b4', opacity=0.85, line=dict(width=1.2, color='#0f172a')),
                name=str(r['doktorAdSoyad']),
                hovertemplate='doktorAdSoyad=%{text}<br>hasta_sayisi=%{x}<br>toplam=%{y:.2f}<extra></extra>',
            )
        )
    else:
        fig_cost_patient = px.scatter(
            doc_perf,
            x='hasta_sayisi',
            y='toplam',
            size='balon_boyutu',
            color='doktorAdSoyad',
            hover_name='doktorAdSoyad',
            hover_data={'hasta_sayisi': ':.0f', 'hasta_basi_maliyet': ':.2f', 'toplam': ':.2f'},
            title='Maliyet & Hasta Sayisi Iliskisi (Balon: Hasta Basi Maliyet)',
        )
    fig_cost_patient.update_layout(
        xaxis_title='hastaAdSoyad',
        yaxis_title='toplam',
        template='plotly_white',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    fig_cost_patient.update_traces(marker=dict(sizemin=8, opacity=0.78, line=dict(width=0.8, color='rgba(0,0,0,0.25)')))
    scatter_debug = {
        'ham_kayit': int(len(df)),
        'nokta_sayisi': int(len(doc_perf)),
        'toplam_maliyet': float(doc_perf['toplam'].sum()) if not doc_perf.empty else 0.0,
    }

    # Stratejik notlar (Kategori 1: Gunluk tuketim ve hiz analizi)
    en_yuksek_brans = "Bilinmiyor"
    if not branch_sum.empty:
        en_yuksek_brans = str(branch_sum.iloc[0]['bransAdi'] or "Bilinmiyor")

    son_hiz = daily['5_Gunluk_Ort'].dropna()
    son_hiz_degeri = float(son_hiz.iloc[-1]) if not son_hiz.empty else 0.0

    en_yogun_satir = daily.loc[daily['dusumMiktar'].idxmax()] if not daily.empty else None
    en_yogun_tarih = str(en_yogun_satir['dusumTarih']) if en_yogun_satir is not None else "-"

    stratejik_notlar = [
        {
            'i18n_key': 'En yuksek malzeme gideri {0} bransinda gerceklesti.',
            'args': [en_yuksek_brans],
            'text': f"En yuksek malzeme gideri {en_yuksek_brans} bransinda gerceklesti.",
        },
        {
            'i18n_key': '5 gunluk hareketli ortalamaya gore tuketim hizi gunluk {0} adet seviyesinde.',
            'args': [f"{son_hiz_degeri:.0f}"],
            'text': f"5 gunluk hareketli ortalamaya gore tuketim hizi gunluk {son_hiz_degeri:.0f} adet seviyesinde.",
        },
        {
            'i18n_key': 'En yogun tuketim gunu: {0}.',
            'args': [en_yogun_tarih],
            'text': f"En yogun tuketim gunu: {en_yogun_tarih}.",
        },
    ]

    # Kategori 2: Tetkik (islem) bazli malzeme detayi
    df['tetkikAdi'] = df['tetkikAdi'].fillna('TANIMSIZ ISLEM').astype(str)
    tetkik_toplam = (
        df.groupby('tetkikAdi', dropna=False)
        .agg(
            toplam=('toplam', 'sum'),
            dusumMiktar=('dusumMiktar', 'sum'),
            malzemeCesidi=('stokAd', 'nunique'),
        )
        .reset_index()
        .sort_values('toplam', ascending=False)
    )
    tetkik_options = tetkik_toplam['tetkikAdi'].tolist()

    tum_islemler_key = '__ALL__'
    selected_tetkik = request.args.get('tetkik', type=str) or tum_islemler_key
    valid_tetkik_values = [tum_islemler_key] + tetkik_options
    if selected_tetkik not in valid_tetkik_values:
        selected_tetkik = tum_islemler_key

    if selected_tetkik == tum_islemler_key:
        secili_df = df.copy()
    else:
        secili_df = df[df['tetkikAdi'] == selected_tetkik].copy()
    tetkik_detay = pd.DataFrame()
    if not secili_df.empty:
        tetkik_detay = (
            secili_df.groupby('stokAd', dropna=False)
            .agg({'dusumMiktar': 'sum', 'toplam': 'sum'})
            .reset_index()
            .sort_values('toplam', ascending=False)
        )

    # Kategori 5: Genel stok tuketim siralamasi
    stok_rank = (
        df.groupby('stokAd', dropna=False)
        .agg({'toplam': 'sum', 'dusumMiktar': 'sum'})
        .reset_index()
        .sort_values('toplam', ascending=False)
        .head(25)
    )
    stok_rank['stokAd'] = stok_rank['stokAd'].fillna('BILINMEYEN STOK').astype(str)

    # Kategori 6 & 7: Depo mevcut + miad verisi
    mevcut_durum_rows = []
    mevcut_kpi = {'toplam_kalem': 0, 'kritik_seviye': 0, 'yeterli_stok': 0, 'stoksuz': 0}
    miad_rows = []
    miad_kpi = {'toplam_kalem': 0, 'miadi_gecmis': 0, 'miadi_yaklasan': 0, 'guvenli': 0}
    miad_unique_seri_parti = 0

    if active_kategori in ('6', '7'):
        if depo_df is not None and not depo_df.empty:
            # --- Kategori 6: Malzeme Mevcut Durum ---
            mevcut_grp = (
                depo_df.groupby('shStokAd', dropna=False)
                .agg(
                    mevcutMiktar=('shMevcutMiktar', 'sum'),
                    minSeviye=('minStokMiktar', 'first'),
                    maxSeviye=('maxStokMiktar', 'first'),
                    kritikSeviye=('kritikStokMiktar', 'first'),
                )
                .reset_index()
                .rename(columns={'shStokAd': 'stokAd'})
                .sort_values('stokAd', ascending=True)
            )

            def _durum(row):
                if row['mevcutMiktar'] <= 0:
                    return 'Stoksuz'
                if row['mevcutMiktar'] < 50:
                    return 'Tedarik Edilmeli'
                if row['kritikSeviye'] > 0 and row['mevcutMiktar'] <= row['kritikSeviye']:
                    return 'Kritik'
                if row['minSeviye'] > 0 and row['mevcutMiktar'] <= row['minSeviye']:
                    return 'Kritik'
                return 'Yeterli'

            mevcut_grp['durum'] = mevcut_grp.apply(_durum, axis=1)
            mevcut_durum_rows = mevcut_grp.to_dict(orient='records')
            mevcut_kpi = {
                'toplam_kalem': int(len(mevcut_grp)),
                'kritik_seviye': int(((mevcut_grp['durum'] == 'Kritik') | (mevcut_grp['durum'] == 'Tedarik Edilmeli')).sum()),
                'yeterli_stok': int((mevcut_grp['durum'] == 'Yeterli').sum()),
                'stoksuz': int((mevcut_grp['durum'] == 'Stoksuz').sum()),
            }

            # --- Kategori 7: Miad Seviye Denetim ---
            miad_df = depo_df[depo_df['shVadeTarih'].notna()].copy()
            if not miad_df.empty:
                bugun = pd.Timestamp(datetime.now().date())
                sinir_90 = bugun + pd.Timedelta(days=90)

                def _miad_durum(vade):
                    if pd.isna(vade):
                        return 'Guvenli'
                    if vade < bugun:
                        return 'Gecmis'
                    if vade <= sinir_90:
                        return 'Yaklasan'
                    return 'Guvenli'

                miad_df['durum'] = miad_df['shVadeTarih'].apply(_miad_durum)
                miad_df['skt'] = miad_df['shVadeTarih'].dt.strftime('%d.%m.%Y')
                miad_result = miad_df[['shStokAd', 'shStokKod', 'shMevcutMiktar', 'skt', 'durum']].copy()
                miad_result = miad_result.rename(columns={
                    'shStokAd': 'stokAd',
                    'shStokKod': 'lotNo',
                    'shMevcutMiktar': 'miktar',
                })
                miad_result = miad_result.sort_values('skt', ascending=True)
                miad_rows = miad_result.to_dict(orient='records')
                miad_kpi = {
                    'toplam_kalem': int(len(miad_result)),
                    'miadi_gecmis': int((miad_result['durum'] == 'Gecmis').sum()),
                    'miadi_yaklasan': int((miad_result['durum'] == 'Yaklasan').sum()),
                    'guvenli': int((miad_result['durum'] == 'Guvenli').sum()),
                }
                miad_unique_seri_parti = int(
                    miad_result['lotNo'].replace('', pd.NA).dropna().nunique()
                )

    charts = {
        'fig_trend': fig_trend.to_html(full_html=False, include_plotlyjs=False),
        'fig_branch_rank': fig_branch_rank.to_html(full_html=False, include_plotlyjs=False),
        'fig_branch_doc_pie': fig_branch_doc_pie.to_html(full_html=False, include_plotlyjs=False),
        'fig_cost_patient': fig_cost_patient.to_html(full_html=False, include_plotlyjs=False),
    }

    return render_template('malzeme.html',
        start_date=sd, end_date=ed, no_data=no_data,
        toplam_tuketim=df['dusumMiktar'].sum(), tekil_hasta=df['hastaAdSoyad'].nunique(),
        farkli_malzeme=df['stokAd'].nunique(), toplam_tutar=df['toplam'].sum(),
        charts=charts, stratejik_notlar=stratejik_notlar,
        no_data_1_5=no_data_1_5,
        no_data_6_7=no_data_6_7,
        no_data_6_7_message=no_data_6_7_message,
        active_kategori=active_kategori,
        tetkik_options=tetkik_options,
        selected_tetkik=selected_tetkik,
        tum_islemler_key=tum_islemler_key,
        brans_options=brans_options,
        selected_brans=selected_brans,
        brans_debug=brans_debug,
        secili_islem_maliyeti=float(secili_df['toplam'].sum()) if not secili_df.empty else 0.0,
        secili_malzeme_cesidi=int(secili_df['stokAd'].nunique()) if not secili_df.empty else 0,
        tetkik_detay_rows=tetkik_detay.to_dict(orient='records'),
        stok_rank_rows=stok_rank.to_dict(orient='records'),
        scatter_debug=scatter_debug,
        mevcut_durum_rows=mevcut_durum_rows,
        mevcut_kpi=mevcut_kpi,
        miad_rows=miad_rows,
        miad_kpi=miad_kpi,
        miad_unique_seri_parti=miad_unique_seri_parti,
        depo_options=depo_options,
        selected_depo=selected_depo,
    )
