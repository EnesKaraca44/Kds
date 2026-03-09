import streamlit as st
import pandas as pd
import plotly.express as px
import utils 
from database.appointment_loaders import load_appointment_data


st.set_page_config(page_title="Hekim & Randevu Analizi", page_icon="🗓️", layout="wide")

if not st.session_state.get("password_correct", False):
    st.warning("🔒 Lütfen Ana Sayfa'dan giriş yapın.")
    st.stop()


sd = st.session_state.get('start_date')
ed = st.session_state.get('end_date')

if not sd or not ed:
    st.error("📅 Lütfen Ana Sayfa'dan bir tarih aralığı seçin.")
    st.stop()


df_raw = load_appointment_data(sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d'))

if df_raw.empty:
    st.info("ℹ️ Seçilen tarih aralığında randevu kaydı bulunamadı.")
    st.stop()


df = df_raw.copy()
df['Trh'] = pd.to_datetime(df['Trh'])


st.title("🗓️ Hekim Randevu & Sadakat Analizi")
utils.aktif_donem_goster()


status_counts = df['Durum'].value_counts()
hizmet_alan = status_counts.get('Geldi', 0) + status_counts.get('Geç Geldi', 0)
gelmeyen = status_counts.get('Gelmedi', 0)
sadakat_orani = (hizmet_alan / len(df) * 100) if len(df) > 0 else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Toplam Randevu", utils.format_turkish_number(len(df), 0))
m2.metric("Genel Sadakat Oranı", f"%{sadakat_orani:.1f}", 
          delta=f"%{100-sadakat_orani:.1f} Kayıp", delta_color="inverse")
m3.metric("Hizmete Dönüşen", utils.format_turkish_number(hizmet_alan, 0))
m4.metric("Aktif Hekim Sayısı", df['dktad'].nunique())

st.divider()


doc_sum = df.groupby('dktad').agg(
    Toplam=('RandevuID', 'size'),
    Hizmet=('Durum', lambda x: x.isin(['Geldi', 'Geç Geldi']).sum()),
    Gelmedi=('Durum', lambda x: (x == 'Gelmedi').sum())
).reset_index()
doc_sum['Sadakat_Orani'] = (doc_sum['Hizmet'] / doc_sum['Toplam'] * 100)


tab_hekim, tab_kanal, tab_smart = st.tabs(["👨‍⚕️ Hekim Performansı", "📍 Kanal & Poliklinik", "🤖 Akıllı Yorumlar"])

with tab_hekim:
    num_selection = st.slider("Grafikte Gösterilecek Hekim Sayısı:", 5, 50, 15)
    top_docs = doc_sum.nlargest(num_selection, 'Sadakat_Orani')
    
    st.plotly_chart(px.bar(top_docs, x='Sadakat_Orani', y='dktad', orientation='h',
                           color='Sadakat_Orani', color_continuous_scale='YlGn',
                           title=f"Sadakat Oranı En Yüksek {num_selection} Hekim"), use_container_width=True)



with tab_kanal:
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.pie(df['SrvAd'].value_counts().nlargest(10).reset_index(), 
                               values='count', names='SrvAd', title="En Yoğun 10 Poliklinik", hole=0.4), use_container_width=True)
    with c2:
        st.plotly_chart(px.bar(df['Randevuverilme_Yeri'].value_counts().reset_index(), 
                               x='count', y='Randevuverilme_Yeri', orientation='h', title="Randevu Kanalları"), use_container_width=True)

with tab_smart:
    st.subheader("🤖 Operasyonel İçgörüler")
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        st.info(f"Kurum genelinde randevuların %{sadakat_orani:.1f} kadarı hizmete dönüşüyor.")
        if gelmeyen > 0:
            top_noshow = df[df['Durum'] == 'Gelmedi'].groupby('SrvAd').size().idxmax()
            st.error(f"⚠️ En fazla randevu kaybı (No-show) **{top_noshow}** polikliniğinde.")

    with col_n2:
        st.success("✅ Öneri: Sadakat oranı %70'in altında kalan hekimler için SMS onay sistemi zorunlu hale getirilebilir.")

utils.footer_ekle()