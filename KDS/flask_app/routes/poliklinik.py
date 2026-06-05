from flask import Blueprint, render_template, request, jsonify
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required
from database.poliklinik_sorgular import (
    poliklinik_performans_verisi_yukle,
    basvuru_sayilari_yukle,
    basvuru_satir_aylik_serisi,
)
from routes.dashboard import get_date_range

poliklinik_bp = Blueprint('poliklinik', __name__)

PAGE_SQL_KODLARI = [
    "poliklinik.poliklinik_performans_verisi_yukle",
    "poliklinik.basvuru_klinik_dagilim",
    "poliklinik.basvuru_hekim_dagilim",
    "poliklinik.basvuru_sevk_turu_dagilim",
    "poliklinik.basvuru_brans_dagilim",
    "poliklinik.basvuru_serisi",
]

_PERF_CHART_LIMIT = 15


def _tr_int(v):
    """Tam sayıları binlik ayırıcı ile göster (tr-TR)."""
    if v is None or pd.isna(v):
        return "0"
    return f"{int(round(float(v))):,}".replace(",", ".")


def _perf_axis_title(sort_by):
    if sort_by == "Benzersiz_Hasta_Sayisi":
        return "Benzersiz hasta sayısı"
    return "Kayıt sayısı"


def _perf_bar_labels(series):
    return [_tr_int(x) for x in series]


def _build_perf_bar_charts(doc_perf, sort_by, limit=_PERF_CHART_LIMIT):
    """En yüksek / en düşük hekimler — çubuk üzerinde gerçek metrik değeri."""
    metric = sort_by
    axis_title = _perf_axis_title(metric)
    top_df = doc_perf.nlargest(limit, metric).sort_values(metric, ascending=True)
    top_fig = px.bar(
        top_df,
        x=metric,
        y="DOKTOR_ADI",
        orientation="h",
        text=top_df[metric],
    )
    top_fig.update_traces(
        marker_color="#3b82f6",
        marker_line=dict(color="#1d4ed8", width=1),
        text=_perf_bar_labels(top_df[metric]),
        texttemplate="%{text}",
        textposition="inside",
        insidetextanchor="end",
        textfont=dict(color="white", size=12),
    )
    top_fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, zeroline=False, title=axis_title),
        yaxis=dict(showgrid=False, zeroline=False, title=""),
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
    )

    top_names = set(top_df["DOKTOR_ADI"])
    bot_pool = doc_perf[(doc_perf[metric] > 0) & (~doc_perf["DOKTOR_ADI"].isin(top_names))]
    if bot_pool.empty:
        bot_pool = doc_perf[doc_perf[metric] > 0]
    bot_df = bot_pool.nsmallest(limit, metric).sort_values(metric, ascending=True)
    bot_fig = px.bar(
        bot_df,
        x=metric,
        y="DOKTOR_ADI",
        orientation="h",
        text=bot_df[metric],
    )
    bot_fig.update_traces(
        marker_color="#fca5a5",
        marker_line=dict(color="#f87171", width=1),
        text=_perf_bar_labels(bot_df[metric]),
        texttemplate="%{text}",
        textposition="inside",
        insidetextanchor="end",
        textfont=dict(color="#7f1d1d", size=12),
    )
    bot_fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, zeroline=False, title=axis_title),
        yaxis=dict(showgrid=False, zeroline=False, title=""),
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return top_fig, bot_fig


def _extract_hour(value):
    text = str(value).strip()
    if not text or text.lower() == 'nan': #Eğer yazı tamamen boşsa işlemi durdur.
        return None

    
    # "09:15" veya "2025-01-05 09:15:00" gibi değerlerde 2025 yerine 9'u bulmayı tercih eder.
    match = re.search(r'([01]?\d|2[0-3])(?=:)', text)
    if match:
        return int(match.group(1))  #Bu bir kuraldır: "Ya 0 ile 19 arası bir sayı bul ya da 20 ile 23 arası bir sayı bul" der.

    exact = re.fullmatch(r'([01]?\d|2[0-3])', text)
    if exact:
        return int(exact.group(1))  #Eğer yukarıdaki kurala uygun bir şey bulunduysa içeri gir.

    return None


_BASVURU_CATEGORY_TITLES = {
    "ozet_klinik": "BAŞVURU SAYILARI",
    "brans": "BRANŞLARA GÖRE DAĞILIM",
    "sevk_tur": "SEVK TÜRLERİNE GÖRE DAĞILIM",
    "hekim": "HEKİMLERE GÖRE BAŞVURU SAYILARI",
}


@poliklinik_bp.route('/poliklinik/basvuru-serisi')
@login_required
def basvuru_serisi():
    """Basvuru tablosu satir tiklamasi: son 6 ay aylik adet serisi."""
    sd, ed = get_date_range()
    category = (request.args.get("category") or "").strip()
    ad = (request.args.get("ad") or "").strip()
    months = request.args.get("months", type=int) or 1
    months = max(1, min(months, 6))

    if category not in _BASVURU_CATEGORY_TITLES or not ad:
        return jsonify({"labels": [], "values": [], "period_total": 0, "months": months})

    try:
        labels, values = basvuru_satir_aylik_serisi(
            category,
            ad,
            ed.strftime("%Y-%m-%d"),
            6,
        )
        slice_count = min(months, len(values))
        period_total = sum(int(v or 0) for v in values[-slice_count:]) if slice_count else 0
        payload = {
            "labels": [str(x) for x in labels],
            "values": [int(v or 0) for v in values],
            "period_total": int(period_total),
            "months": months,
            "category_title": _BASVURU_CATEGORY_TITLES.get(category, ""),
        }
    except Exception as exc:
        print(f"Basvuru serisi hatasi: {exc}")
        payload = {"labels": [], "values": [], "period_total": 0, "months": months}

    return jsonify(payload)


@poliklinik_bp.route('/poliklinik')
@login_required
def poliklinik():
    sd, ed = get_date_range()
    df_raw = poliklinik_performans_verisi_yukle(sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d'))

    if df_raw.empty:
        return render_template('poliklinik.html', start_date=sd, end_date=ed, no_data=True, page_sql_kodlari=PAGE_SQL_KODLARI)

    # Toplam metrikler için ham veriyi kullanıyoruz (BELİRTİLMEMİŞ dahil)
    df = df_raw.copy()
    toplam_kayit = len(df)
    benzersiz_hasta = df['HstKod'].nunique()
    brans_sayisi = df['SrvAd'].nunique()

    # Grafiklerde 'BELİRTİLMEMİŞ' olanları görmek istemediğimiz için filtreleme yapıyoruz
    df_filtered = df[df['DOKTOR_ADI'].str.upper().str.strip() != 'BELİRTİLMEMİŞ'].copy()
    aktif_hekim = df_filtered['DOKTOR_ADI'].nunique()

    doc_perf = df_filtered.groupby('DOKTOR_ADI').agg(
        Kayit_Sayisi=('DOKTOR_ADI', 'size'),
        Benzersiz_Hasta_Sayisi=('HstKod', 'nunique')
    ).reset_index()

    # Sıralama için sorgu parametreleri (varsayılan: benzersiz hasta)
    sort_by = request.args.get('sort', 'Benzersiz_Hasta_Sayisi')
    if sort_by not in ['Kayit_Sayisi', 'Benzersiz_Hasta_Sayisi', 'Hekim_Bazli_Hasta_Sayilari']:
        sort_by = 'Benzersiz_Hasta_Sayisi'

    # Tab 1: Performans Sıralaması (Top / Bottom 15)
    hekim_hasta_table = []
    hekim_hasta_toplam = 0

    if not doc_perf.empty and sort_by != 'Hekim_Bazli_Hasta_Sayilari':
        fig_top, fig_bot = _build_perf_bar_charts(doc_perf, sort_by)

        #Eğer kullanıcı grafik değil de "Ben tüm listeyi tablo olarak görmek istiyorum" dediyse burası çalışır.
    elif sort_by == 'Hekim_Bazli_Hasta_Sayilari':
        # Resimdeki tablo: tüm hekimler + benzersiz hasta sayısı
        table_df = (
            doc_perf[['DOKTOR_ADI', 'Benzersiz_Hasta_Sayisi']]
            .sort_values(['Benzersiz_Hasta_Sayisi', 'DOKTOR_ADI'], ascending=[False, True])
            .copy()
        )
         #Listedeki tüm hasta sayılarını toplayıp genel toplamı bulur.
        #Tabloyu satır satır okur ve hekim_hasta_table sepetine ekler.
        hekim_hasta_toplam = int(table_df['Benzersiz_Hasta_Sayisi'].sum()) if not table_df.empty else 0
        hekim_hasta_table = [
            {"ad": str(r["DOKTOR_ADI"]), "toplam": int(r["Benzersiz_Hasta_Sayisi"])}
            for _, r in table_df.iterrows()
        ]
        fig_top = px.bar(title="").update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)')
        fig_bot = px.bar(title="").update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)')
    else:
        fig_top = px.bar(title="Veri Bulunamadı").update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)')
        fig_bot = px.bar(title="Veri Bulunamadı").update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)')

    # Tab 2: Haftalık Gün Dağılımı
    gun_tr = {
        'Monday': 'Pazartesi', 'Tuesday': 'Salı', 'Wednesday': 'Çarşamba',
        'Thursday': 'Perşembe', 'Friday': 'Cuma', 'Saturday': 'Cumartesi', 'Sunday': 'Pazar'
    }
    df['Gun_Adı'] = df['KAYIT_TARIHI'].dt.day_name().map(gun_tr)
    gun_sirasi = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
    
    daily_avg = df.groupby('Gun_Adı').size().reindex(gun_sirasi).reset_index(name='Hasta Sayısı').fillna(0)
    fig_days = px.bar(daily_avg, x='Gun_Adı', y='Hasta Sayısı', color='Hasta Sayısı', 
                      color_continuous_scale='Turbo') # title Handled by HTML
    fig_days.update_layout(
        template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, zeroline=False, title=""),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)', zeroline=False, title="Hasta Sayısı"),
        coloraxis_showscale=False,
        margin=dict(l=40, r=20, t=60, b=40)
    )

    # Tab 2: Kurum dağılımı
    kurum_data = df.groupby('KrmAdi').size().reset_index(name='Sayi').nlargest(10, 'Sayi')
    if not kurum_data.empty: #Veri varsa bir pasta grafiği çizer.
        fig_kurum = px.pie(kurum_data, values='Sayi', names='KrmAdi', hole=0.5,
                           color_discrete_sequence=px.colors.qualitative.Bold) # title Handled by HTML
        fig_kurum.update_traces(textinfo='percent+label', textposition='outside')
        fig_kurum.update_layout(
            template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.1),
            margin=dict(l=20, r=150, t=60, b=40)
        )
    else:
        fig_kurum = px.pie(title="Veri Bulunamadı").update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)')

    # Tab 2: Günlük trend
    # Tüm tarihleri dolduralım
    all_dates = pd.date_range(start=sd, end=ed).date
    daily_raw = df.groupby(df['KAYIT_TARIHI'].dt.date).size().reset_index(name='Sayi')
    daily_trend = pd.DataFrame({'KAYIT_TARIHI': all_dates})
    #Yarattığımız boş takvim ile gerçek hasta sayılarını birleştirir.
    daily_trend = pd.merge(daily_trend, daily_raw, on='KAYIT_TARIHI', how='left').fillna(0)
    daily_trend['Sayi'] = daily_trend['Sayi'].astype(int)
    #7 günlük hareketli ortalama hesaplar. Bu, günlük iniş çıkışlardaki gürültüyü siler
    daily_trend['Hareketli_Ortalama'] = daily_trend['Sayi'].rolling(window=7, min_periods=1).mean()
    peak_day = daily_trend.loc[daily_trend['Sayi'].idxmax()] #idxmax(): Veri içindeki en yüksek (tepe) noktayı bulur.
    trend_avg = float(daily_trend['Sayi'].mean()) if not daily_trend.empty else 0.0

    last_day = daily_trend.iloc[-1]

    fig_trend = go.Figure()
    fig_trend.add_trace(
        go.Scatter(
            x=daily_trend['KAYIT_TARIHI'],
            y=daily_trend['Sayi'],
            mode='lines',
            name='Gunluk Trend',
            line=dict(color='rgba(59, 130, 246, 0.45)', width=1.8),
            fill='tozeroy', #Çizgi grafiğinin altını hafif bir mavi renkle boyar.
            fillcolor='rgba(59, 130, 246, 0.10)',
            hovertemplate='Tarih: %{x}<br>Basvuru: %{y}<extra></extra>',
        )
    )
    fig_trend.add_trace(
        go.Scatter(
            x=daily_trend['KAYIT_TARIHI'],
            y=daily_trend['Hareketli_Ortalama'],
            mode='lines',
            name='7 Gunluk Ortalama',
            line=dict(color='#f59e0b', width=2, dash='dash'),
            hovertemplate='Tarih: %{x}<br>7 Gunluk Ort: %{y:.1f}<extra></extra>',
        )
    )
    fig_trend.add_trace(
        go.Scatter(
            x=[peak_day['KAYIT_TARIHI'], last_day['KAYIT_TARIHI']],
            y=[peak_day['Sayi'], last_day['Sayi']],
            mode='markers+text',
            name='Kilit Noktalar',
            text=[f"Tepe: {int(peak_day['Sayi'])}", f"Son: {int(last_day['Sayi'])}"],
            textposition=['top center', 'top left'],
            marker=dict(size=10, color=['#dc2626', '#16a34a'], line=dict(color='white', width=1)),
            hovertemplate='Tarih: %{x}<br>Basvuru: %{y}<extra></extra>',
        )
    )
    fig_trend.update_layout(
        template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        # title='Gunluk Basvuru Trendi', # Handled by HTML
        hovermode='x unified',
        xaxis=dict(
            showgrid=True, gridcolor='rgba(15,23,42,0.05)', zeroline=False, title="",
            tickformat='%b %Y',
            rangeselector=dict(
                buttons=[
                    dict(count=1, label='1A', step='month', stepmode='backward'),
                    dict(count=3, label='3A', step='month', stepmode='backward'),
                    dict(count=6, label='6A', step='month', stepmode='backward'),
                    dict(step='all', label='Tum Donem'),
                ]
            ),
        ),
        yaxis=dict(showgrid=True, gridcolor='rgba(15,23,42,0.08)', zeroline=False, title="Basvuru Sayisi"),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=40, r=20, t=70, b=40),
        shapes=[  #Grafiğin tam ortasından yatay, kesik bir çizgi geçirir. Bu çizgi, tüm dönemin ortalama hasta sayısını temsil eder.
            dict(
                type='line',
                xref='paper',
                x0=0,
                x1=1,
                y0=trend_avg,
                y1=trend_avg,
                line=dict(color='rgba(245, 158, 11, 0.5)', width=1, dash='dot'),
            )
        ]
    )

    # Tab 3: Yoğunluk Analizi (Line Chart)
    #09:15" verisinden 9 rakamını çeker.
    df['Saat_H'] = df['Saat'].apply(_extract_hour)
    df['Saat_H'] = df['Saat_H'].fillna(-1).astype(int)
    
    saat_traffic = df[df['Saat_H'].between(0, 23)].groupby('Saat_H').size().reset_index(name='Sayi')
    
    # Sadece 0 ile 23 arasındaki geçerli saatleri alır, her saatte kaç hasta geldiğini sayar.
    tum_saatler = pd.DataFrame({'Saat_H': range(24)})
    saat_traffic = pd.merge(tum_saatler, saat_traffic, on='Saat_H', how='left').fillna(0)
    saat_traffic['Sayi'] = saat_traffic['Sayi'].astype(int)
    
    saat_traffic['Saat_Baslangic'] = saat_traffic['Saat_H'].apply(lambda x: f"{int(x):02d}")
    #idxmax(): Günün en yoğun saatini (zirve noktasını) bulur.
    peak_hour = saat_traffic.loc[saat_traffic['Sayi'].idxmax()] 
    hourly_avg = float(saat_traffic['Sayi'].mean()) if not saat_traffic.empty else 0.0
    top_hours = set(saat_traffic.nlargest(3, 'Sayi')['Saat_H'].tolist())
    bar_colors = ['#1d4ed8' if h in top_hours else '#93c5fd' for h in saat_traffic['Saat_H']]

     #Sütun (Bar) Grafiği Çizimi
    fig_hourly = go.Figure()
    fig_hourly.add_trace(
        go.Bar(
            x=saat_traffic['Saat_H'],
            y=saat_traffic['Sayi'],
            name='Saatlik Hacim',
            marker=dict(
                color=bar_colors,
                line=dict(color='rgba(255,255,255,0.9)', width=0.6),
            ),
            hovertemplate='Saat: %{x:02d}:00<br>Hasta: %{y}<extra></extra>',
        )
    )
    #Çizgi (Scatter) Grafiği Ekleme
    fig_hourly.add_trace(
        go.Scatter(
            x=saat_traffic['Saat_H'],
            y=saat_traffic['Sayi'],
            mode='lines+markers',
            name='Akis Cizgisi',
            line=dict(color='#1e3a8a', width=2.5, shape='spline'),
            marker=dict(size=6, color='#1e40af'),
            hovertemplate='Saat: %{x:02d}:00<br>Hasta: %{y}<extra></extra>',
        )
    )
    #Ortalama Çizgisi ve Tasarım Detayları
    fig_hourly.add_trace(
        go.Scatter(
            x=[0, 23],
            y=[hourly_avg, hourly_avg],
            mode='lines',
            name='Saatlik Ortalama',
            line=dict(color='rgba(245, 158, 11, 0.8)', width=2, dash='dot'),
            hovertemplate='Ortalama: %{y:.1f}<extra></extra>',
        )
    )
    fig_hourly.update_layout(
        template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        # title='Gun Ici Saatlik Hasta Trafigi
        hovermode='x unified',
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            title="Saat Dilimi",
            tickmode='array',
            tickvals=list(range(24)),
            ticktext=[f"{h:02d}" for h in range(24)],
        ),
        yaxis=dict(showgrid=True, gridcolor='rgba(15,23,42,0.08)', zeroline=False, title="Hasta Sayisi"),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=20, r=20, t=60, b=30),
        #İşaretlemeler (Annotations) ve Gölgelendirme
        annotations=[
            dict(
                x=peak_hour['Saat_H'],
                y=peak_hour['Sayi'],
                text=f"En Yogun Saat: {peak_hour['Saat_Baslangic']}:00",
                showarrow=True,
                arrowhead=2,
                ax=30,
                ay=-30,
                bgcolor='rgba(255,255,255,0.92)',
                bordercolor='#93c5fd',
            )
        ],
        shapes=[ #Grafiğin arka planında, 08:00 ile 17:00 arasını çok hafif bir renkle boyar.
            dict(
                type='rect',
                xref='x',
                yref='paper',
                x0=8,
                x1=17,
                y0=0,
                y1=1,
                fillcolor='rgba(59, 130, 246, 0.05)',
                line=dict(width=0),
                layer='below',
            ),
            dict(
                type='line',
                xref='x',
                x0=0,
                x1=23,
                y0=hourly_avg,
                y1=hourly_avg,
                line=dict(color='rgba(30, 64, 175, 0.35)', width=1, dash='dot'),
            )
        ]
    )

    # Tab 4: Hekim Detay (Dropdown + Metrics + Pie Chart)
    #sayfadaki aşağı açılır listeden (dropdown) bir doktor seçilmesini sağlar
    hekim_list = sorted([str(x) for x in df_filtered['DOKTOR_ADI'].dropna().unique()])
    selected_hekim = request.args.get('hekim')
    if not selected_hekim and hekim_list:
        selected_hekim = hekim_list[0]

    hekim_toplam_kayit = 0
    hekim_brans_sayisi = 0
    fig_hekim_pie = None

#Seçilen doktorun hastanedeki performans detayları burada hesaplanır.
    if selected_hekim and selected_hekim in hekim_list:
        df_hekim = df_filtered[df_filtered['DOKTOR_ADI'] == selected_hekim]
        hekim_toplam_kayit = len(df_hekim)
        hekim_brans_sayisi = df_hekim['SrvAd'].nunique()
        
        brans_dagilimi = df_hekim.groupby('SrvAd').size().reset_index(name='Sayi')
        fig_hekim_pie = px.pie(brans_dagilimi, values='Sayi', names='SrvAd', hole=0.0) # title Handled by HTML
        fig_hekim_pie.update_traces(textinfo='percent', textposition='inside')
        fig_hekim_pie.update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

     #Hazırlanan tüm grafikler web sayfasında görüntülenebilmesi için HTML formatına çevrilir.
    charts = {
        'fig_top': fig_top.to_html(full_html=False, include_plotlyjs=False),
        'fig_bot': fig_bot.to_html(full_html=False, include_plotlyjs=False),
        'fig_kurum': fig_kurum.to_html(full_html=False, include_plotlyjs=False),
        'fig_days': fig_days.to_html(full_html=False, include_plotlyjs=False),
        'fig_trend': fig_trend.to_html(full_html=False, include_plotlyjs=False),
        'fig_hourly': fig_hourly.to_html(full_html=False, include_plotlyjs=False),
        'fig_hekim_pie': fig_hekim_pie.to_html(full_html=False, include_plotlyjs=False) if fig_hekim_pie else "",
    }
    #Bu kısım, yöneticinin en önemli veriyi tek bakışta görmesi için kısa bir özet metni hazırlar.
    insight_text = ""
    if not doc_perf.empty:
        if sort_by == 'Hekim_Bazli_Hasta_Sayilari':
            top_data_sorted = doc_perf.sort_values(['Benzersiz_Hasta_Sayisi', 'DOKTOR_ADI'], ascending=[False, True])
            top_doc_name = top_data_sorted.iloc[0]['DOKTOR_ADI']
            top_doc_val = int(top_data_sorted.iloc[0]['Benzersiz_Hasta_Sayisi'])
            insight_text = f"INSIGHT_MAX_VAL|{top_doc_val}|{top_doc_name}"
        else:
            top_data_sorted = doc_perf.sort_values(sort_by, ascending=False)
            top_doc_name = top_data_sorted.iloc[0]['DOKTOR_ADI']
            top_doc_val = int(top_data_sorted.iloc[0][sort_by])
            metric_label = "kayıt" if sort_by == 'Kayit_Sayisi' else "benzersiz hasta"
            insight_text = f"INSIGHT_TOP_PERF|{top_doc_val}|{metric_label}|{top_doc_name}"

    basvuru = basvuru_sayilari_yukle(sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d'))

#Tüm hesaplamalar biter ve her şey poliklinik.html isimli tasarım dosyasına gönderilir.
    return render_template('poliklinik.html',
        start_date=sd, end_date=ed, no_data=False,
        toplam_kayit=toplam_kayit, benzersiz_hasta=benzersiz_hasta,
        aktif_hekim=aktif_hekim, brans_sayisi=brans_sayisi,
        charts=charts, current_sort=sort_by, insight_text=insight_text,
        hekim_list=hekim_list, selected_hekim=selected_hekim, 
        hekim_toplam_kayit=hekim_toplam_kayit, hekim_brans_sayisi=hekim_brans_sayisi,
        hekim_hasta_table=hekim_hasta_table, hekim_hasta_toplam=hekim_hasta_toplam,
        basvuru=basvuru,
        page_sql_kodlari=PAGE_SQL_KODLARI,
    )
