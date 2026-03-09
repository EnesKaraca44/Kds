from flask import Blueprint, render_template, request
import pandas as pd
import plotly.express as px
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required
from database.polyclinic_loaders import load_polyclinic_performance_data
from routes.dashboard import get_date_range

poliklinik_bp = Blueprint('poliklinik', __name__)


@poliklinik_bp.route('/poliklinik')
@login_required
def poliklinik():
    sd, ed = get_date_range()
    df_raw = load_polyclinic_performance_data(sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d'))

    if df_raw.empty:
        return render_template('poliklinik.html', start_date=sd, end_date=ed, no_data=True)

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

    # Query Parameters for sorting
    sort_by = request.args.get('sort', 'Kayit_Sayisi')
    if sort_by not in ['Kayit_Sayisi', 'Benzersiz_Hasta_Sayisi']:
        sort_by = 'Kayit_Sayisi'

    # Tab 1: Performans Sıralaması (Top / Bottom 15)
    if not doc_perf.empty:
        top_data = doc_perf.nlargest(15, sort_by).sort_values(sort_by, ascending=True)
        fig_top = px.bar(top_data, x=sort_by, y='DOKTOR_ADI', orientation='h', 
                         color=sort_by, color_continuous_scale='Blues', text_auto='.0f',
                         title=f"En Çok Hasta Bakan Hekimler")
        fig_top.update_layout(
            template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=True),
            yaxis=dict(showgrid=False, zeroline=False, title=""),
            coloraxis_showscale=False,
            margin=dict(l=20, r=20, t=40, b=20)
        )

        bot_data = doc_perf[doc_perf[sort_by] > 0].nsmallest(15, sort_by).sort_values(sort_by, ascending=False)
        fig_bot = px.bar(bot_data, x=sort_by, y='DOKTOR_ADI', orientation='h', 
                         color=sort_by, color_continuous_scale='Reds', text_auto='.0f',
                         title=f"En Düşük Hasta Bakan Hekimler")
        fig_bot.update_layout(
            template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=True),
            yaxis=dict(showgrid=False, zeroline=False, title=""),
            coloraxis_showscale=False,
            margin=dict(l=20, r=20, t=40, b=20)
        )
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
                      color_continuous_scale='Turbo', title="Haftalık Gün Dağılımı")
    fig_days.update_layout(
        template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, zeroline=False, title=""),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)', zeroline=False, title="Hasta Sayısı"),
        coloraxis_showscale=False,
        margin=dict(l=40, r=20, t=60, b=40)
    )

    # Tab 2: Kurum dağılımı
    kurum_data = df.groupby('KrmAdi').size().reset_index(name='Sayi').nlargest(10, 'Sayi')
    if not kurum_data.empty:
        fig_kurum = px.pie(kurum_data, values='Sayi', names='KrmAdi', hole=0.5,
                           color_discrete_sequence=px.colors.qualitative.Bold,
                           title="Kurum / Sigorta Dağılımı")
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
    daily_trend = pd.merge(daily_trend, daily_raw, on='KAYIT_TARIHI', how='left').fillna(0)
    
    fig_trend = px.area(daily_trend, x='KAYIT_TARIHI', y='Sayi', color_discrete_sequence=['#1f77b4'],
                        title="Günlük Başvuru Trendi")
    fig_trend.update_traces(line_width=1.5, fillcolor='rgba(31, 119, 180, 0.3)')
    fig_trend.update_layout(
        template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.03)', zeroline=False, title=""),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)', zeroline=False, title="Sayı"),
        margin=dict(l=40, r=20, t=60, b=40)
    )

    # Tab 3: Yoğunluk Analizi (Line Chart)
    # Original Streamlit logic: df['Saat'].str[:2]
    # Here we clean the Saat column just in case.
    df['Saat_Clean'] = df['Saat'].astype(str).str.strip().str.extract(r'^(\d+)').fillna(0).astype(int)
    # Above regex extracts digits at start, e.g., '08:45' -> '08' -> 8.
    df['Saat_H'] = df['Saat_Clean'].apply(lambda x: x if 0 <= x <= 23 else 0)
    
    saat_traffic = df.groupby('Saat_H').size().reset_index(name='Sayi')
    
    # Tüm 24 saati garanti altına alalım
    tum_saatler = pd.DataFrame({'Saat_H': range(24)})
    saat_traffic = pd.merge(tum_saatler, saat_traffic, on='Saat_H', how='left').fillna(0)
    saat_traffic['Sayi'] = saat_traffic['Sayi'].astype(int)
    
    # Streamlit ile aynı olması için Saat_H'yi string (00, 01, 02...) yapalım ki X-axis sıralı ve temiz olsun
    saat_traffic['Saat_Baslangic'] = saat_traffic['Saat_H'].apply(lambda x: f"{int(x):02d}")
    
    fig_hourly = px.line(saat_traffic, x='Saat_Baslangic', y='Sayi', markers=True,
                         title="Gün İçi Saatlik Hasta Trafiği",
                         labels={'Saat_Baslangic': 'Saat', 'Sayi': 'Hasta Sayısı'})
    fig_hourly.update_traces(line_shape='spline', line_color='#3b82f6')
    fig_hourly.update_layout(
        template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, zeroline=False, title="Saat Dilimi"),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)', zeroline=False, title="Hasta Sayısı"),
        margin=dict(l=20, r=20, t=40, b=20)
    )

    # Tab 4: Hekim Detay (Dropdown + Metrics + Pie Chart)
    hekim_list = sorted([str(x) for x in df_filtered['DOKTOR_ADI'].dropna().unique()])
    selected_hekim = request.args.get('hekim')
    if not selected_hekim and hekim_list:
        selected_hekim = hekim_list[0]

    hekim_toplam_kayit = 0
    hekim_brans_sayisi = 0
    fig_hekim_pie = None

    if selected_hekim and selected_hekim in hekim_list:
        df_hekim = df_filtered[df_filtered['DOKTOR_ADI'] == selected_hekim]
        hekim_toplam_kayit = len(df_hekim)
        hekim_brans_sayisi = df_hekim['SrvAd'].nunique()
        
        brans_dagilimi = df_hekim.groupby('SrvAd').size().reset_index(name='Sayi')
        fig_hekim_pie = px.pie(brans_dagilimi, values='Sayi', names='SrvAd', hole=0.0,
                               title=f"{selected_hekim} Branş Dağılımı")
        fig_hekim_pie.update_traces(textinfo='percent', textposition='inside')
        fig_hekim_pie.update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    charts = {
        'fig_top': fig_top.to_html(full_html=False, include_plotlyjs=False),
        'fig_bot': fig_bot.to_html(full_html=False, include_plotlyjs=False),
        'fig_kurum': fig_kurum.to_html(full_html=False, include_plotlyjs=False),
        'fig_days': fig_days.to_html(full_html=False, include_plotlyjs=False),
        'fig_trend': fig_trend.to_html(full_html=False, include_plotlyjs=False),
        'fig_hourly': fig_hourly.to_html(full_html=False, include_plotlyjs=False),
        'fig_hekim_pie': fig_hekim_pie.to_html(full_html=False, include_plotlyjs=False) if fig_hekim_pie else "",
    }

    insight_text = ""
    if not doc_perf.empty:
        top_data_sorted = doc_perf.sort_values(sort_by, ascending=False)
        top_doc_name = top_data_sorted.iloc[0]['DOKTOR_ADI']
        top_doc_val = top_data_sorted.iloc[0][sort_by]
        metric_label = "Kayıt Sayısı" if sort_by == 'Kayit_Sayisi' else "Benzersiz Hasta Sayısı"
        insight_text = f"Seçili dönemde en yüksek performansı gösteren hekim {top_doc_val} {metric_label} ile {top_doc_name} olmuştur."

    return render_template('poliklinik.html',
        start_date=sd, end_date=ed, no_data=False,
        toplam_kayit=toplam_kayit, benzersiz_hasta=benzersiz_hasta,
        aktif_hekim=aktif_hekim, brans_sayisi=brans_sayisi,
        charts=charts, current_sort=sort_by, insight_text=insight_text,
        hekim_list=hekim_list, selected_hekim=selected_hekim, 
        hekim_toplam_kayit=hekim_toplam_kayit, hekim_brans_sayisi=hekim_brans_sayisi
    )
