import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import utils
import time
from database.denture_loaders import load_prosthetic_performance_data


st.set_page_config(page_title="Protez Stratejik Analiz", page_icon="🦷", layout="wide")

if not st.session_state.get("password_correct", False):
    st.warning("🔒 Lütfen Ana Sayfa'dan giriş yapın.")
    st.stop()


sd = st.session_state.get('start_date')
ed = st.session_state.get('end_date')

if not sd or not ed:
    st.error("📅 Tarih aralığı seçilmedi.")
    st.stop()

with st.spinner("Protez verileri analiz ediliyor..."):
    df_raw = load_prosthetic_performance_data(sd, ed)

if df_raw is None or df_raw.empty:
    st.info("👋 Seçilen aralıkta analiz edilecek veri bulunamadı.")
    st.stop()


df = df_raw.copy()
df.columns = [str(c).upper().strip().replace(' ', '_') for c in df.columns]

def find_column(candidates, df_cols):
    for c in candidates:
        if c.upper() in df_cols: return c.upper()
    return None


C_HEKIM = find_column(['HEKIM_ADI', 'HEKIMAD', 'DKTAD', 'DOKTOR_ADI'], df.columns)
C_PLAN = find_column(['PLANLANANTESLIMSURESI', 'PLAN_SURE', 'HEDEF_GUN', 'PLANLANAN_SURE'], df.columns)
C_GERCEK = find_column(['ORTALAMA_TESLIM_SURESI', 'ORTALAMA_TESLIM_SÜRESI', 'TESLIM_SURE_GUN', 'GERCEK_SURE'], df.columns)
C_SUT = find_column(['SUT_ADI', 'PROTEZADI', 'ACIKLAMA', 'ISLEM_ADI'], df.columns)
C_HASTA = find_column(['HASTA_ADI', 'HASTA', 'ADI_SOYADI', 'HASTAADI'], df.columns)
C_HSTKOD = find_column(['HSTKOD', 'HASTA_KODU', 'DOSYA_NO', 'HASTAKODU'], df.columns) # Hasta Kodu Eklendi
C_TARIH = find_column(['TEDAVI_TARIHI', 'PLAN_TARIHI', 'TARIH', 'KAYIT_TARIHI'], df.columns)


df['PLAN'] = pd.to_numeric(df[C_PLAN], errors='coerce').fillna(0).round(0).astype(int)
df['GERCEK'] = pd.to_numeric(df[C_GERCEK], errors='coerce').fillna(0).round(1)
df['GECIKME_GUN'] = (df['GERCEK'] - df['PLAN']).clip(lower=0).round(1)

st.sidebar.header("🔍 Analiz Ayarları")
kritik_limit = st.sidebar.number_input("Kritik Gün Eşiği", min_value=0, value=30, step=1)
tum_hekimler = df[C_HEKIM].unique()
hekim_limit = st.sidebar.slider("Gösterilecek Hekim Sayısı", 1, len(tum_hekimler), min(10, len(tum_hekimler)))

top_hekimler = df[C_HEKIM].value_counts().head(hekim_limit).index.tolist()
df_f = df[df[C_HEKIM].isin(top_hekimler)].copy()


st.title("🦷 Protez Süreç Performans Paneli")
utils.aktif_donem_goster()

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Filtrelenmiş Vaka", len(df_f))
with m2:
    gecikme_oranı = (len(df_f[df_f['GECIKME_GUN'] > 0]) / len(df_f)) * 100 if len(df_f) > 0 else 0
    st.metric("Gecikme Oranı", f"%{gecikme_oranı:.1f}")
with m3:
    kritik_sayi = len(df_f[df_f['GERCEK'] > kritik_limit])
    st.metric(f"{kritik_limit} Gün Üzeri", kritik_sayi)
with m4:
    ort_teslim = df_f['GERCEK'].mean()
    st.metric("Ort. Teslimat", f"{ort_teslim:.1f} Gün")

st.divider()


t1, t2, t3, t4 = st.tabs(["📊 Genel Performans", "🚩 Geciken Hekim Listesi", "👤 Hasta Detayları", "📈 Trend Analizi"])

with t1:
    col1, col2 = st.columns(2)
    with col1:
        comp_df = df_f.groupby(C_HEKIM)[['PLAN', 'GERCEK']].mean().round(1).reset_index().sort_values('GERCEK', ascending=False)
        fig_h = go.Figure()
        fig_h.add_trace(go.Bar(x=comp_df[C_HEKIM], y=comp_df['PLAN'], name='Hedef', marker_color='#3498db', text=comp_df['PLAN'], textposition='auto'))
        fig_h.add_trace(go.Bar(x=comp_df[C_HEKIM], y=comp_df['GERCEK'], name='Gerçek', marker_color='#e74c3c', text=comp_df['GERCEK'], textposition='auto'))
        fig_h.update_layout(title="Hekim Bazlı Süre (Hedef vs Gerçek)", barmode='group')
        st.plotly_chart(fig_h, use_container_width=True)
    
    with col2:
        sut_risk = df_f.groupby(C_SUT)['GECIKME_GUN'].mean().round(1).sort_values(ascending=False).head(10).reset_index()
        fig_s = px.bar(sut_risk, x='GECIKME_GUN', y=C_SUT, orientation='h', title="En Çok Geciken 10 İşlem (Ort. Gün)",
                        color='GECIKME_GUN', color_continuous_scale='Reds', text='GECIKME_GUN')
        st.plotly_chart(fig_s, use_container_width=True)

with t2:
    st.subheader(f"⚠️ Kritik Sınırı ({kritik_limit} Gün) Aşan Vakalar")
    kritik_df = df_f[df_f['GERCEK'] > kritik_limit]
    if not kritik_df.empty:
        h_ozet = kritik_df.groupby(C_HEKIM).agg({
            C_HASTA: 'count', 
            'GERCEK': 'mean', 
            'GECIKME_GUN': 'sum'
        }).reset_index()
        
        h_ozet.columns = ['Hekim', 'Kritik Vaka Sayısı', 'Ort. Teslim Süresi', 'Toplam Gecikme (Gün)']
        
      
        h_ozet['Ort. Teslim Süresi'] = h_ozet['Ort. Teslim Süresi'].round(1)
        h_ozet['Toplam Gecikme (Gün)'] = h_ozet['Toplam Gecikme (Gün)'].round(0).astype(int)

        st.dataframe(
            h_ozet.sort_values('Kritik Vaka Sayısı', ascending=False)
            .style.background_gradient(cmap='Reds', subset=['Kritik Vaka Sayısı'])
            .format({'Ort. Teslim Süresi': '{:.1f} Gün', 'Toplam Gecikme (Gün)': '{:,.0f} Gün'}), 
            use_container_width=True, hide_index=True
        )
    else:
        st.success("Tebrikler! Kritik sınırı aşan vaka bulunmuyor.")

with t3:
    st.subheader("🔍 Hekim ve Hasta Bazlı Detay Sorgulama")
    secilen_h = st.selectbox("Hekim Detay Sorgula:", top_hekimler)
    h_data = df_f[df_f[C_HEKIM] == secilen_h].copy()
    
    f_gecikme = st.toggle("Sadece gecikenleri göster", value=True)
    if f_gecikme: h_data = h_data[h_data['GECIKME_GUN'] > 0]
    
   
    h_data['GERCEK'] = h_data['GERCEK'].round(1)
    h_data['GECIKME_GUN'] = h_data['GECIKME_GUN'].round(1)

   
    display_cols = []
    if C_HSTKOD: display_cols.append(C_HSTKOD)
    if C_HASTA: display_cols.append(C_HASTA)
    display_cols.extend([C_SUT, 'PLAN', 'GERCEK', 'GECIKME_GUN'])

    st.dataframe(
        h_data[display_cols].sort_values('GERCEK', ascending=False),
        use_container_width=True, hide_index=True
    )

with t4:
    if C_TARIH:
        df_f['HAFTA_DT'] = pd.to_datetime(df_f[C_TARIH], dayfirst=True, errors='coerce')
        df_trend_data = df_f.dropna(subset=['HAFTA_DT']).copy()
        if not df_trend_data.empty:
            df_trend_data['Hafta'] = df_trend_data['HAFTA_DT'].dt.to_period('W').apply(lambda r: r.start_time)
            trend_df = df_trend_data.groupby('Hafta')['GECIKME_GUN'].mean().round(1).reset_index()
            fig_trend = px.line(trend_df, x='Hafta', y='GECIKME_GUN', title="Haftalık Ortalama Gecikme Trendi", markers=True)
            st.plotly_chart(fig_trend, use_container_width=True)


st.divider()
st.subheader("🤖 Stratejik Analiz Özeti")
if not df_f.empty:
    worst_sut = sut_risk.iloc[0][C_SUT] if not sut_risk.empty else 'Veri Yok'
    st.info(f"""
    * **Operasyonel Verimlilik:** Ortalama teslimat süreniz **{ort_teslim:.1f}** gün seviyesinde.
    * **Darboğaz Tespiti:** En çok gecikme yaşanan işlem: **{worst_sut}**.
    * **Hekim Performansı:** Kritik eşiği en çok aşan hekimler listede kırmızı ile vurgulanmıştır.
    """)

utils.footer_ekle()