import streamlit as st
import pandas as pd
import plotly.express as px
import utils
from database.healthcarewaste_loaders import load_medical_waste_data


st.set_page_config(page_title="Tıbbi Atık Analizi", page_icon="♻️", layout="wide")


if not st.session_state.get("password_correct", False):
    st.warning("🔒 Lütfen Ana Sayfa'dan giriş yapın.")
    st.stop()

st.title("♻️ Tıbbi Atık Analizi")
utils.aktif_donem_goster()


sd = st.session_state.get('start_date')
ed = st.session_state.get('end_date')

if not sd or not ed:
    st.error("📅 Lütfen tarih seçiniz.")
    st.stop()

with st.spinner("Atık verileri getiriliyor..."):
    df = load_medical_waste_data(sd, ed)

if df.empty:
    st.info("ℹ️ Seçilen dönemde tıbbi atık verisi bulunamadı.")
    st.stop()


df.columns = [c.upper().strip() for c in df.columns]
aylar = ['OCAK', 'ŞUBAT', 'MART', 'NİSAN', 'MAYIS', 'HAZİRAN', 
         'TEMMUZ', 'AĞUSTOS', 'EYLÜL', 'EKİM', 'KASIM', 'ARALIK']
mevcut_aylar = [ay for ay in aylar if ay in df.columns]


total_val = df['TOPLAM'].sum()
aylik_ort = total_val / len(mevcut_aylar) if mevcut_aylar else 0

m1, m2, m3 = st.columns(3)
m1.metric("Toplam Atık Miktarı", f"{utils.format_turkish_number(total_val)} kg")
m2.metric("Aylık Ortalama", f"{utils.format_turkish_number(aylik_ort)} kg")
m3.metric("Birim Sayısı", len(df))

st.divider()


tab_tablo, tab_grafik, tab_heatmap = st.tabs(["📊 Veri Tablosu", "📈 Trend Analizi", "🔥 Yoğunluk Haritası"])

with tab_tablo:
    st.subheader("Birim Bazlı Aylık Dağılım")
    st.dataframe(df[['HESAP_PLANI_TANIMI'] + mevcut_aylar + ['TOPLAM']], 
                 use_container_width=True, hide_index=True)

with tab_grafik:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        trend_df = df[mevcut_aylar].sum().reset_index()
        trend_df.columns = ['AY', 'MIKTAR']
        fig_trend = px.line(trend_df, x='AY', y='MIKTAR', markers=True, 
                            title="Aylık Toplam Atık Seyri",
                            category_orders={"AY": aylar})
        st.plotly_chart(fig_trend, use_container_width=True)
    
    with col2:
        fig_pie = px.pie(df.nlargest(10, 'TOPLAM'), values='TOPLAM', names='HESAP_PLANI_TANIMI', 
                         title="En Çok Atık Üreten 10 Birim", hole=0.3)
        st.plotly_chart(fig_pie, use_container_width=True)

with tab_heatmap:
    st.subheader("Birimlerin Aylık Atık Yoğunluğu")
    heat_df = df.set_index('HESAP_PLANI_TANIMI')[mevcut_aylar]
    fig_heat = px.imshow(heat_df, color_continuous_scale='Reds', aspect="auto")
    st.plotly_chart(fig_heat, use_container_width=True)


st.divider()
with st.expander("🤖 Sistem Analiz Notları", expanded=True):
    insights = utils.get_dynamic_insights(df, label_col='HESAP_PLANI_TANIMI', value_col='TOPLAM')
    for ins in insights:
        st.info(ins)

utils.footer_ekle()