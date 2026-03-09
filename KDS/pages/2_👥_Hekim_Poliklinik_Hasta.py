import streamlit as st
import pandas as pd
import plotly.express as px
import utils
from database.polyclinic_loaders import load_polyclinic_performance_data


st.set_page_config(page_title="Poliklinik Analizi", page_icon="👥", layout="wide")

if not st.session_state.get("password_correct", False):
    st.warning("🔒 Lütfen Ana Sayfa'dan giriş yapın.")
    st.stop()

sd = st.session_state.get('start_date')
ed = st.session_state.get('end_date')

if not sd or not ed:
    st.error("📅 Lütfen Ana Sayfa'dan bir tarih aralığı seçin.")
    st.stop()

df_raw = load_polyclinic_performance_data(sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d'))

if df_raw.empty:
    st.info("ℹ️ Seçilen tarih aralığında poliklinik verisi bulunamadı.")
    st.stop()

df = df_raw.copy()
df = df[df['DOKTOR_ADI'] != 'BELİRTİLMEMİŞ']


st.title("👥 Hekim Poliklinik Hasta Analizi")
utils.aktif_donem_goster()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Toplam Pol. Kaydı", utils.format_turkish_number(len(df), 0))
m2.metric("Benzersiz Hasta", utils.format_turkish_number(df['HstKod'].nunique(), 0))
m3.metric("Aktif Hekim", df['DOKTOR_ADI'].nunique())
m4.metric("Hizmet Veren Branş", df['SrvAd'].nunique())

st.divider()


doc_perf = df.groupby('DOKTOR_ADI').agg(
    Kayıt_Sayısı=('DOKTOR_ADI', 'size'),
    Hasta_Sayısı=('HstKod', 'nunique')
).reset_index()

top_n = st.sidebar.slider("Grafiklerdeki Hekim Sayısı", 5, 50, 10, 5)


tab_perf, tab_trend, tab_density, tab_detay = st.tabs([
    "🏆 Hasta Sayısı Analizi", 
    "📈 Zaman & Kurum Dağılımı", 
    "⏰ Yoğunluk Analizi",
    "🔍 Hekim Detay"
])

with tab_perf:
    metric_choice = st.radio("Sıralama Kriteri:", ["Kayıt Sayısı", "Benzersiz Hasta Sayısı"], horizontal=True)
    sort_col = "Kayıt_Sayısı" if metric_choice == "Kayıt Sayısı" else "Hasta_Sayısı"
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader(f"🔝 En Çok Hasta Bakan Hekimler")
        top_data = doc_perf.nlargest(top_n, sort_col)
        fig_top = px.bar(top_data, x=sort_col, y='DOKTOR_ADI', orientation='h', color=sort_col, 
                         color_continuous_scale='Greens', text_auto=True)
        fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_top, use_container_width=True)
        
    with c2:
        st.subheader(f"🔻 En Düşük Hasta Bakan Hekimler")
        bot_data = doc_perf[doc_perf[sort_col] > 0].nsmallest(top_n, sort_col)
        fig_bot = px.bar(bot_data, x=sort_col, y='DOKTOR_ADI', orientation='h', color=sort_col, 
                         color_continuous_scale='Reds_r', text_auto=True)
        fig_bot.update_layout(yaxis={'categoryorder':'total descending'})
        st.plotly_chart(fig_bot, use_container_width=True)

with tab_trend:
    col_tr1, col_tr2 = st.columns(2)
    
    with col_tr1:
        st.subheader("📅 Haftalık Gün Dağılımı")
       
        gun_tr = {
            'Monday': 'Pazartesi', 'Tuesday': 'Salı', 'Wednesday': 'Çarşamba',
            'Thursday': 'Perşembe', 'Friday': 'Cuma', 'Saturday': 'Cumartesi', 'Sunday': 'Pazar'
        }
        df['Gun_Adı'] = df['KAYIT_TARIHI'].dt.day_name().map(gun_tr)
        gun_sirasi = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
        
        daily_avg = df.groupby('Gun_Adı').size().reindex(gun_sirasi).reset_index(name='Hasta Sayısı')
        fig_days = px.bar(daily_avg, x='Gun_Adı', y='Hasta Sayısı', color='Hasta Sayısı', color_continuous_scale='Blues')
        st.plotly_chart(fig_days, use_container_width=True)

    with col_tr2:
        st.subheader("🏢 Kurum / Sigorta Dağılımı")
        kurum_data = df.groupby('KrmAdi').size().reset_index(name='Sayi').nlargest(10, 'Sayi')
        fig_kurum = px.pie(kurum_data, values='Sayi', names='KrmAdi', hole=0.4, 
                           color_discrete_sequence=px.colors.qualitative.Prism)
        fig_kurum.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_kurum, use_container_width=True)

    st.divider()
    st.subheader("📈 Günlük Başvuru Trendi")
    daily_trend = df.groupby(df['KAYIT_TARIHI'].dt.date).size().reset_index(name='Sayi')
    st.plotly_chart(px.area(daily_trend, x='KAYIT_TARIHI', y='Sayi', color_discrete_sequence=['#1f77b4']), use_container_width=True)

with tab_density:
    st.subheader("⏰ Gün İçi Saatlik Hasta Trafiği")
    df['Saat_Baslangic'] = df['Saat'].str[:2]
    hourly = df.groupby('Saat_Baslangic').size().reset_index(name='Hasta Sayısı')
    fig_hour = px.line(hourly, x='Saat_Baslangic', y='Hasta Sayısı', markers=True, title="Saatlik Yoğunluk")
    st.plotly_chart(fig_hour, use_container_width=True)

with tab_detay:
    sel_doc = st.selectbox("Analiz İçin Hekim Seçin:", ["Seçiniz..."] + sorted(df['DOKTOR_ADI'].unique().tolist()))
    if sel_doc != "Seçiniz...":
        h_df = df[df['DOKTOR_ADI'] == sel_doc]
        c_dr1, c_dr2 = st.columns([1, 2])
        with c_dr1:
            st.metric("Hekim Toplam Kayıt", len(h_df))
            st.metric("Branş Sayısı", h_df['SrvAd'].nunique())
        with c_dr2:
            st.plotly_chart(px.pie(h_df, names='SrvAd', title=f"{sel_doc} Branş Dağılımı"), use_container_width=True)

# --- 4. ALT BİLGİ ---
st.subheader("🤖 Akıllı Yorumlar")
insights = utils.get_dynamic_insights(doc_perf, 'DOKTOR_ADI', sort_col)
for insight in insights:
    st.write(insight)

utils.footer_ekle()