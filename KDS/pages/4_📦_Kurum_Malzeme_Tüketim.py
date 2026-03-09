import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import utils 
from database.stock_loaders import load_stock_consumption_data


st.set_page_config(page_title="Kurum Malzeme Tüketim", page_icon="📦", layout="wide")

if not st.session_state.get("password_correct", False):
    st.warning("🔒 Lütfen Ana Sayfa'dan giriş yapın.")
    st.stop()


sd = st.session_state.get('start_date')
ed = st.session_state.get('end_date')

if not sd or not ed:
    st.error("📅 Lütfen Ana Sayfa'dan bir tarih aralığı seçin.")
    st.stop()

df_raw = load_stock_consumption_data(sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d'))

if df_raw is None or df_raw.empty:
    st.info("ℹ️ Seçilen tarih aralığında malzeme tüketim kaydı bulunamadı.")
    st.stop()


df = df_raw.copy()
df['dusumTarih'] = pd.to_datetime(df['dusumTarih']).dt.date
df['toplam'] = pd.to_numeric(df['toplam'], errors='coerce').fillna(0).round(2)
df['dusumMiktar'] = pd.to_numeric(df['dusumMiktar'], errors='coerce').fillna(0).round(0)


daily = df.groupby('dusumTarih')['dusumMiktar'].sum().reset_index().sort_values('dusumTarih')
daily['5_Gunluk_Ort'] = daily['dusumMiktar'].rolling(window=5).mean().round(1)


st.title("📦 Kurum Malzeme Tüketim Analizi")
utils.aktif_donem_goster()

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Toplam Tüketim", f"{utils.format_turkish_number(df['dusumMiktar'].sum(), 0)} Adet")
with m2:
    st.metric("Tekil Hasta", f"{df['hastaAdSoyad'].nunique()} Kişi")
with m3:
    st.metric("Farklı Malzeme", f"{df['stokAd'].nunique()} Kalem")
with m4:
    st.metric("Toplam Tutar", f"₺{utils.format_turkish_number(df['toplam'].sum(), 2)}")

st.divider()


tab_trend, tab_islem, tab_branch, tab_doctor, tab_stok = st.tabs([
    "📈 Tüketim Trendi", 
    "🧪 İşlem Bazlı Stok", 
    "🏥 Branş & Hekim Dağılımı", 
    "👨‍⚕️ Hekim Verimliliği", 
    "📋 Stok Detay"
])


with tab_trend:
    st.subheader("📊 Günlük Tüketim ve Hız Analizi")
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(x=daily['dusumTarih'], y=daily['dusumMiktar'], name='Günlük Tüketim', marker_color='#3498db'))
    fig_trend.add_trace(go.Scatter(x=daily['dusumTarih'], y=daily['5_Gunluk_Ort'], name='5 Günlük Ortalama (Hız)', 
                                  line=dict(color='#e74c3c', width=3, dash='dot')))
    fig_trend.update_layout(xaxis_title="Tarih", yaxis_title="Adet", hovermode="x unified")
    st.plotly_chart(fig_trend, use_container_width=True)


with tab_islem:
    st.subheader("🔗 Tetkik (İşlem) Bazlı Malzeme Detayı")
    df_islem = df.dropna(subset=['tetkikAdi'])
    if not df_islem.empty:
        # Hata Önleyici: None değerleri temizleyip sıralıyoruz
        available_tests = sorted([t for t in df_islem['tetkikAdi'].unique() if t is not None])
        selected_tetkik = st.selectbox("Analiz edilecek işlemi seçin:", available_tests)
        
        is_df = df_islem[df_islem['tetkikAdi'] == selected_tetkik]
        
        ca, cb = st.columns([1, 2])
        ca.metric("İşlem Maliyeti", f"₺{is_df['toplam'].sum():,.2f}")
        ca.metric("Malzeme Çeşidi", is_df['stokAd'].nunique())
        
        g_cols = ['stokAd']
        if 'birim' in df.columns: g_cols.append('birim')
        is_stok = is_df.groupby(g_cols).agg({'dusumMiktar':'sum', 'toplam':'sum'}).reset_index().sort_values('toplam', ascending=False)
        cb.dataframe(is_stok.style.format({'toplam': '₺{:,.2f}', 'dusumMiktar': '{:,.0f}'}), use_container_width=True, hide_index=True)
    else:
        st.warning("Tetkik verisi bulunamadı.")


with tab_branch:
    st.subheader("🏥 Branş ve Branş İçi Hekim Analizi")
    col_br1, col_br2 = st.columns(2)
    
    with col_br1:
        branch_sum = df.groupby('bransAdi')['toplam'].sum().reset_index().sort_values('toplam', ascending=False).head(10)
        fig_br = px.bar(branch_sum, x='toplam', y='bransAdi', orientation='h', title="En Çok Tüketen 10 Branş (₺)",
                        color='toplam', color_continuous_scale='Reds')
        st.plotly_chart(fig_br, use_container_width=True)
        
    with col_br2:
      
        available_branches = sorted([b for b in df['bransAdi'].unique() if b is not None])
        selected_br = st.selectbox("Branş İçi Hekim Dağılımı İçin Seçin:", available_branches)
        
        br_df = df[df['bransAdi'] == selected_br]
        br_doc = br_df.groupby('doktorAdSoyad')['toplam'].sum().reset_index().sort_values('toplam', ascending=False)
        fig_pie = px.pie(br_doc.head(10), values='toplam', names='doktorAdSoyad', title=f"{selected_br} Hekim Payları", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)


with tab_doctor:
    st.subheader("👨‍⚕️ Hekim Bazında Hasta Başı Maliyet")
    doc_perf = df.groupby('doktorAdSoyad').agg({'dusumMiktar':'sum', 'toplam':'sum', 'hastaAdSoyad':'nunique'}).reset_index()
    doc_perf['hasta_basi_maliyet'] = (doc_perf['toplam'] / doc_perf['hastaAdSoyad']).round(2)
    fig_sc = px.scatter(doc_perf, x='hastaAdSoyad', y='toplam', size='hasta_basi_maliyet', color='doktorAdSoyad',
                        title="Maliyet & Hasta Sayısı İlişkisi (Balon: Hasta Başı Maliyet)")
    st.plotly_chart(fig_sc, use_container_width=True)


with tab_stok:
    st.subheader("📋 Genel Stok Tüketim Sıralaması")
    st_cols = ['stokAd']
    if 'birim' in df.columns: st_cols.append('birim')
    stok_list = df.groupby(st_cols).agg({'toplam':'sum', 'dusumMiktar':'sum'}).reset_index().sort_values('toplam', ascending=False).head(25)
    st.dataframe(stok_list.style.format({'toplam': '₺{:,.2f}'}), use_container_width=True, hide_index=True)


st.divider()
st.subheader("🤖 Stratejik Denetim Notları")
if not daily.empty:
    top_br_name = branch_sum.iloc[0]['bransAdi'] if not branch_sum.empty else "Belirlenemedi"
    notes = [
        f"📍 En yüksek malzeme gideri **{top_br_name}** branşında gerçekleşti.",
        f"📈 5 günlük hareketli ortalamaya göre tüketim hızı günlük **{daily['5_Gunluk_Ort'].iloc[-1]:.0f}** adet seviyesinde.",
        f"⚠️ En yoğun tüketim günü: **{daily.loc[daily['dusumMiktar'].idxmax()]['dusumTarih']}**."
    ]
    for n in notes: st.info(n)

utils.footer_ekle()