import streamlit as st
import pandas as pd
import plotly.express as px
import utils 
from database.patient_loaders import load_foreign_patient_data


st.set_page_config(page_title="Yabancı Hasta Analizi", page_icon="🌍", layout="wide")


if not st.session_state.get("password_correct", False):
    st.warning("🔒 Lütfen Ana Sayfa'dan giriş yapın.")
    st.stop()


sd = st.session_state.get('start_date')
ed = st.session_state.get('end_date')

if not sd or not ed:
    st.error("📅 Lütfen Ana Sayfa'dan bir tarih aralığı seçin.")
    st.stop()


df_raw = load_foreign_patient_data(sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d'))

if df_raw.empty:
    st.info("ℹ️ Seçilen tarih aralığında yabancı hasta kaydı bulunamadı.")
    st.stop()


df = df_raw.copy()
df['Fiyat'] = pd.to_numeric(df['Fiyat'], errors='coerce').fillna(0)


st.title("🌍 Yabancı Hasta Verileri Analizi")
utils.aktif_donem_goster()


total_patients = df['HastaAdi'].nunique()
total_revenue = df['Fiyat'].sum()
avg_rev = total_revenue / total_patients if total_patients > 0 else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Toplam Yabancı Hasta", utils.format_turkish_number(total_patients, 0))
m2.metric("Toplam Gelir (₺)", utils.format_turkish_number(total_revenue, 2))
m3.metric("Hasta Başı Ort. Gelir", utils.format_turkish_number(avg_rev, 2))
m4.metric("Ülke Çeşitliliği", df['Ulke'].nunique())

st.divider()


country_summary = df.groupby('Ulke').agg(
    Hasta_Sayisi=('HastaAdi', 'nunique'),
    Toplam_Gelir=('Fiyat', 'sum')
).reset_index()
country_summary['Hasta_Basi_Gelir'] = country_summary['Toplam_Gelir'] / country_summary['Hasta_Sayisi']


tab_geo, tab_eff, tab_demo = st.tabs(["🗺️ Coğrafi Dağılım", "📊 Verimlilik Matrisi", "👶 Demografi"])

with tab_geo:
    c1, c2 = st.columns(2)
    with c1:
        top_rev = country_summary.nlargest(10, 'Toplam_Gelir')
        st.plotly_chart(px.bar(top_rev, x='Toplam_Gelir', y='Ulke', orientation='h', 
                               title="Gelir Lideri Ülkeler", color='Toplam_Gelir', color_continuous_scale='Viridis'), use_container_width=True)
    with c2:
        st.plotly_chart(px.pie(country_summary.nlargest(10, 'Hasta_Sayisi'), values='Hasta_Sayisi', names='Ulke', 
                               title="Hasta Sayısı Dağılımı", hole=0.4), use_container_width=True)

with tab_eff:
    st.subheader("📈 Ülke Bazlı Verimlilik (Hacim vs. Değer)")
    fig_scatter = px.scatter(
        country_summary, x='Hasta_Sayisi', y='Toplam_Gelir', size='Hasta_Basi_Gelir', color='Ulke',
        hover_name='Ulke', title="Balon Büyüklüğü: Hasta Başına Ortalama Gelir",
        labels={'Hasta_Sayisi': 'Hasta Sayısı', 'Toplam_Gelir': 'Toplam Gelir (₺)'}, template='plotly_white'
    )
    st.plotly_chart(fig_scatter, use_container_width=True)



with tab_demo:
    c1, c2 = st.columns(2)
    with c1:
        if 'YAS' in df.columns:
            st.plotly_chart(px.histogram(df, x='YAS', color='Cinsiyet', barmode='group', title="Yaş ve Cinsiyet Dağılımı"), use_container_width=True)
    with c2:
        st.plotly_chart(px.pie(df, names='Cinsiyet', title="Cinsiyet Payı"), use_container_width=True)


st.subheader("🤖 Akıllı Analiz Notları")
insights = utils.generate_smart_insights(country_summary, 'Ulke', 'Toplam_Gelir', 'Hasta_Sayisi')
for note in insights:
    st.info(note)

utils.footer_ekle()