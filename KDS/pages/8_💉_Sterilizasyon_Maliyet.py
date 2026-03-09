import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import utils
from database.sterilization_loaders import load_sterilization_data


st.set_page_config(page_title="Sterilizasyon Analizi", page_icon="💉", layout="wide")


if not st.session_state.get("password_correct", False):
    st.warning("🔒 Lütfen Ana Sayfa'dan giriş yapın.")
    st.stop()


sd = st.session_state.get('start_date')
ed = st.session_state.get('end_date')

if not sd or not ed:
    st.error("📅 Lütfen Ana Sayfa'dan bir tarih aralığı seçin.")
    st.stop()

df_all = load_sterilization_data(sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d'))

if df_all.empty:
    st.info("ℹ️ Seçilen tarih aralığında sterilizasyon kaydı bulunamadı.")
    st.stop()


df_grouped = df_all.groupby('ServisAdi').agg({
    'Toplam_Maliyet': 'sum',
    'Toplam_Paket': 'sum',
    'Hasta_Sayisi': 'sum'
}).reset_index()


df_grouped['Birim_Maliyet'] = df_grouped.apply(lambda x: x['Toplam_Maliyet'] / x['Toplam_Paket'] if x['Toplam_Paket'] > 0 else 0, axis=1)
df_grouped['Hasta_Basi_Maliyet'] = df_grouped.apply(lambda x: x['Toplam_Maliyet'] / x['Hasta_Sayisi'] if x['Hasta_Sayisi'] > 0 else 0, axis=1)
df_grouped['Hasta_Basi_Paket'] = df_grouped.apply(lambda x: x['Toplam_Paket'] / x['Hasta_Sayisi'] if x['Hasta_Sayisi'] > 0 else 0, axis=1)


st.title("💉 Sterilizasyon Süreç & Verimlilik Analizi")
utils.aktif_donem_goster()

t_maliye = df_grouped['Toplam_Maliyet'].sum()
t_paket = df_grouped['Toplam_Paket'].sum()
t_hasta = df_grouped['Hasta_Sayisi'].sum()
u_ort = t_maliye / t_paket if t_paket > 0 else 0
h_ort_maliyet = t_maliye / t_hasta if t_hasta > 0 else 0

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Toplam Maliyet", f"{utils.format_turkish_number(t_maliye)} ₺")
m2.metric("Birim Paket Maliyeti", f"{u_ort:.2f} ₺")
m3.metric("Toplam Paket Sayısı", utils.format_turkish_number(t_paket, 0))
m4.metric("Toplam Hasta Sayısı", utils.format_turkish_number(t_hasta, 0))
m5.metric("Hst. Başı Ort. Maliyet", f"{h_ort_maliyet:.2f} ₺")

st.divider()


tab_dist, tab_smart, tab_patient, tab_efficiency, tab_raw = st.tabs([
    "📊 Klinik Dağılımı", 
    "🎯 Verimlilik Matrisi", 
    "👥 Hasta & Verimlilik", 
    "🔍 Operasyonel Anomali",
    "📄 Veri Kaydı (Klinik Özet)"
])

with tab_dist:
    st.subheader("🏢 Klinik Bazlı Maliyet Dağılımı")
    num_selection = st.slider("Gösterilecek Klinik Sayısı:", 5, min(len(df_grouped), 50), 15)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        top_clinics = df_grouped.nlargest(num_selection, 'Toplam_Maliyet')
        fig_bar = px.bar(top_clinics, x='ServisAdi', y='Toplam_Maliyet', color='Birim_Maliyet', 
                         color_continuous_scale='Reds', title=f"Maliyet Lideri İlk {num_selection} Klinik")
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        st.write("🎯 **Pareto Analizi**")
        df_p = df_grouped.sort_values('Toplam_Maliyet', ascending=False)
        df_p['Kumulatif'] = df_p['Toplam_Maliyet'].cumsum() / df_p['Toplam_Maliyet'].sum() * 100
        fig_p = go.Figure()
        fig_p.add_trace(go.Bar(x=df_p['ServisAdi'][:10], y=df_p['Toplam_Maliyet'][:10], name="Maliyet"))
        fig_p.add_trace(go.Scatter(x=df_p['ServisAdi'][:10], y=df_p['Kumulatif'][:10], yaxis="y2", name="Pareto %", line=dict(color="red")))
        fig_p.update_layout(yaxis2=dict(overlaying="y", side="right", range=[0, 105]), showlegend=False, height=350)
        st.plotly_chart(fig_p, use_container_width=True)

with tab_smart:
    st.subheader("🎯 Verimlilik Quadrant (Dörtlü Bölge) Analizi")
    avg_paket_maliyet = df_grouped['Birim_Maliyet'].mean()
    avg_hasta_maliyet = df_grouped['Hasta_Basi_Maliyet'].mean()

    fig_smart = px.scatter(
        df_grouped, x="Birim_Maliyet", y="Hasta_Basi_Maliyet", size="Toplam_Maliyet", color="ServisAdi",
        hover_data=['Toplam_Paket', 'Hasta_Sayisi'],
        title="Birim Paket vs. Hasta Başı Maliyet",
        labels={'Birim_Maliyet': 'Paket Başı Maliyet (₺)', 'Hasta_Basi_Maliyet': 'Hasta Başı Maliyet (₺)'}
    )
    fig_smart.add_vline(x=avg_paket_maliyet, line_dash="dash", line_color="gray", annotation_text="Ort. Paket")
    fig_smart.add_hline(y=avg_hasta_maliyet, line_dash="dash", line_color="gray", annotation_text="Ort. Hasta")
    st.plotly_chart(fig_smart, use_container_width=True)

with tab_patient:
    st.subheader("👥 Hasta Başına Kullanım Detayları")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        top_h_maliyet = df_grouped[df_grouped['Hasta_Sayisi'] > 0].nlargest(10, 'Hasta_Basi_Maliyet')
        fig_h1 = px.bar(top_h_maliyet, x='ServisAdi', y='Hasta_Basi_Maliyet', color='Hasta_Basi_Maliyet', color_continuous_scale='Oranges')
        st.plotly_chart(fig_h1, use_container_width=True)
    with col_p2:
        fig_h2 = px.scatter(df_grouped[df_grouped['Hasta_Sayisi'] > 0], x="Hasta_Basi_Paket", y="Hasta_Basi_Maliyet", size="Hasta_Sayisi", color="ServisAdi")
        st.plotly_chart(fig_h2, use_container_width=True)

with tab_efficiency:
    st.subheader("🔍 Yönetici Özet: Operasyonel Anomaliler")
    kurum_ort_paket = df_grouped['Hasta_Basi_Paket'].mean()
    
    col_e1, col_e2 = st.columns([1, 1])
    with col_e1:
        st.write("⚠️ **Yüksek Paket Tüketimi (Ortalamanın > %50 Üstü)**")
        anomali_df = df_grouped[df_grouped['Hasta_Basi_Paket'] > kurum_ort_paket * 1.5].sort_values('Hasta_Basi_Paket', ascending=False)
        if not anomali_df.empty:
            st.warning(f"{len(anomali_df)} klinikte sıra dışı kullanım saptandı.")
            st.dataframe(anomali_df[['ServisAdi', 'Hasta_Basi_Paket', 'Hasta_Basi_Maliyet']], use_container_width=True)
        else:
            st.success("Kullanım oranları tüm kliniklerde stabilize durumda.")

    with col_e2:
        st.write("🏆 **En Verimli Klinikler (Maliyet/Hasta)**")
        verimli_df = df_grouped[df_grouped['Hasta_Sayisi'] > 5].nsmallest(5, 'Hasta_Basi_Maliyet')
        st.dataframe(verimli_df[['ServisAdi', 'Hasta_Basi_Maliyet', 'Birim_Maliyet']], use_container_width=True)


    fig_gap = go.Figure()
    fig_gap.add_trace(go.Bar(x=df_grouped['ServisAdi'], y=df_grouped['Hasta_Sayisi'], name='Hasta Sayısı'))
    fig_gap.add_trace(go.Bar(x=df_grouped['ServisAdi'], y=df_grouped['Toplam_Paket'], name='Paket Sayısı'))
    fig_gap.update_layout(barmode='group', title="Klinik Bazlı İş Yükü ve Kaynak Dengesi")
    st.plotly_chart(fig_gap, use_container_width=True)

with tab_raw:
    st.subheader("📋 Klinik Bazlı Özet Tablo")
    st.dataframe(df_grouped.style.format({
        'Toplam_Maliyet': '{:.2f} ₺', 'Birim_Maliyet': '{:.2f} ₺', 'Hasta_Basi_Maliyet': '{:.2f} ₺',
        'Hasta_Basi_Paket': '{:.2f}', 'Toplam_Paket': '{:,.0f}', 'Hasta_Sayisi': '{:,.0f}'
    }), use_container_width=True)
    
    csv_export = df_grouped.to_csv(index=False, sep=';', decimal=',', encoding='utf-8-sig')
    st.download_button(label="📥 Excel (Türkçe Format) İndir", data=csv_export.encode('utf-8-sig'), 
                       file_name="sterilizasyon_yonetici_raporu.csv", mime="text/csv")

utils.footer_ekle()