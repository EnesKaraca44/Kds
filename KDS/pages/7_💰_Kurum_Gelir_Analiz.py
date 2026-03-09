import streamlit as st
import pandas as pd
import plotly.express as px
import utils 
from database.invoice_loaders import load_invoice_revenue_data


st.set_page_config(page_title="Kurum Gelir Analizi", page_icon="💰", layout="wide")


if not st.session_state.get("password_correct", False):
    st.warning("🔒 Lütfen Ana Sayfa'dan giriş yapın.")
    st.stop()


sd = st.session_state.get('start_date')
ed = st.session_state.get('end_date')

if not sd or not ed:
    st.error("📅 Lütfen Ana Sayfa'dan bir tarih aralığı seçin.")
    st.stop()


df = load_invoice_revenue_data(sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d'))

if df.empty:
    st.info("ℹ️ Seçilen tarih aralığında fatura verisi bulunamadı.")
    st.stop()


df.columns = [c.upper().strip() for c in df.columns]


st.title("💰 Kurum Gelir & Fatura Analizi")
utils.aktif_donem_goster()

t_gelir_kdvli = df['FATURA_KDVLI_TOPLAM_TUTAR'].sum()
t_gelir_net = df['FATURA_TOPLAM_TUTAR'].sum()
t_fatura = df['FATURA_NO'].nunique()
t_kisi = df['FATURA_KISI_SAYISI'].sum()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Toplam Gelir (KDV'li)", f"{utils.format_turkish_number(t_gelir_kdvli)} ₺")
m2.metric("Toplam Fatura", utils.format_turkish_number(t_fatura, 0))
m3.metric("Faturalanan Kişi", utils.format_turkish_number(t_kisi, 0))
m4.metric("Net Gelir", f"{utils.format_turkish_number(t_gelir_net)} ₺")

st.divider()


tab_kurum, tab_trend, tab_detay = st.tabs([
    "🏢 Kurum Performansı", 
    "📈 Gelir Trendi", 
    "📄 Fatura Listesi"
])

with tab_kurum:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏢 Kurum Türüne Göre Gelir")
        kurum_tur_df = df.groupby('KURUM_TURU')['FATURA_KDVLI_TOPLAM_TUTAR'].sum().reset_index()
        fig_pie = px.pie(kurum_tur_df, values='FATURA_KDVLI_TOPLAM_TUTAR', names='KURUM_TURU', 
                         hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.subheader("👤 En Çok Ciro Yapan 10 Kurum/İlgili")
        top_kurum = df.groupby('FATURA_ILGILI')['FATURA_KDVLI_TOPLAM_TUTAR'].sum().nlargest(10).reset_index()
        fig_bar = px.bar(top_kurum, x='FATURA_KDVLI_TOPLAM_TUTAR', y='FATURA_ILGILI', orientation='h',
                         color='FATURA_KDVLI_TOPLAM_TUTAR', color_continuous_scale='GnBu')
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

with tab_trend:
    st.subheader("🗓️ Günlük Fatura Gelir Trendi")
    daily = df.groupby(df['FATURA_TARIHI'].dt.date)['FATURA_KDVLI_TOPLAM_TUTAR'].sum().reset_index()
    daily.columns = ['Tarih', 'Gelir']
    
    fig_trend = px.area(daily, x='Tarih', y='Gelir', title="Günlük KDV Dahil Gelir", markers=True)
    st.plotly_chart(fig_trend, use_container_width=True)

with tab_detay:
    st.subheader("📄 Son 500 Fatura Kaydı")
    st.dataframe(df.sort_values('FATURA_TARIHI', ascending=False).head(500), use_container_width=True)


st.divider()
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("📂 Tüm Veriyi CSV Olarak İndir", csv, "kurum_gelir_analizi.csv", "text/csv")

utils.footer_ekle()