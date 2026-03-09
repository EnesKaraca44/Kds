import streamlit as st
import pandas as pd
import plotly.express as px
import utils
from database.xray_loaders import load_xray_analysis_data


st.set_page_config(page_title="Röntgen & Branş Analizi", page_icon="🦷", layout="wide")


if not st.session_state.get("password_correct", False):
    st.warning("⚠️ Lütfen önce ana sayfadan giriş yapın.")
    st.stop()

sd = st.session_state.get('start_date')
ed = st.session_state.get('end_date')

if not sd or not ed:
    st.error("📅 Lütfen ana sayfadan bir tarih aralığı seçiniz.")
    st.stop()

st.title("🩻 Röntgen Branş ve Verimlilik Analiz Paneli")
utils.aktif_donem_goster()


with st.spinner("🔄 Röntgen verileri analiz ediliyor..."):
    df_raw = load_xray_analysis_data(sd, ed)

if df_raw is None or df_raw.empty:
    st.info(f"ℹ️ {sd} - {ed} aralığında röntgen verisi bulunamadı.")
    st.stop()

df = df_raw.copy()


def find_column(candidates, df_cols):
    for c in candidates:
        clean_c = c.upper().strip()
        for col in df_cols:
            if clean_c == col.upper().replace('_', ' ').strip() or clean_c == col.upper().strip():
                return col
    return None

C_HEKIM = find_column(['DKTAD', 'HEKIM ADI', 'DOKTOR', 'HEKIM'], df.columns)
C_BRANS = find_column(['GSS_KLINIK_ADI', 'KLINIK', 'BRANS'], df.columns)
C_PAN = find_column(['PANORAMIK RÖNTGEN SAYISI', 'PANORAMIK SAYI'], df.columns)
C_PERI = find_column(['PERIAPIKAL RÖNTGEN SAYISI', 'PERIAPIKAL SAYI'], df.columns)
C_SEF = find_column(['SEFALOMETRIK RÖNTGEN SAYISI', 'SEFALOMETRIK SAYI'], df.columns)
C_TOMO = find_column(['DENTAL TOMOGRAFI RÖNTGEN SAYISI', 'TOMOGRAFI SAYI'], df.columns)
C_MUAYENE = find_column(['MUAYENE SAYISI', 'HASTA SAYISI'], df.columns)


film_types = [c for c in [C_PAN, C_PERI, C_SEF, C_TOMO] if c is not None]
all_numeric_cols = film_types + ([C_MUAYENE] if C_MUAYENE else [])
for col in all_numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)


hekim_analiz_all = df.groupby(C_HEKIM)[all_numeric_cols].sum().reset_index()
hekim_analiz_all['TOPLAM_FILM'] = hekim_analiz_all[film_types].sum(axis=1)


hekim_analiz_all = hekim_analiz_all.sort_values('TOPLAM_FILM', ascending=False)


st.sidebar.header("🔍 Filtreler")
num_dr = st.sidebar.slider("Gösterilecek Hekim Sayısı:", 5, len(hekim_analiz_all), 15)
hekim_analiz_filtered = hekim_analiz_all.head(num_dr)


g1, g2, g3 = st.columns(3)
g1.metric("Kurum Toplam Tetkik", f"{int(hekim_analiz_all['TOPLAM_FILM'].sum())} Adet")
g2.metric("🖼️ Toplam Panoramik", f"{int(hekim_analiz_all[C_PAN].sum())} Adet")
g3.metric("📸 Toplam Periapikal", f"{int(hekim_analiz_all[C_PERI].sum())} Adet")
st.divider()


tab1, tab2, tab3, tab4 = st.tabs(["👨‍⚕️ Hekim Analizi", "🏢 Branş Analizi", "🔥 Isı Haritası", "📈 İsteme Verimliliği"])


with tab1:
    top_dr = hekim_analiz_all.iloc[0]
    dr_adi = top_dr[C_HEKIM]
    dr_total = int(top_dr['TOPLAM_FILM'])
    dr_pan = int(top_dr[C_PAN])
    dr_peri = int(top_dr[C_PERI]) if C_PERI in top_dr else 0
    pan_yuzde = (dr_pan / dr_total * 100) if dr_total > 0 else 0
    peri_yuzde = (dr_peri / dr_total * 100) if dr_total > 0 else 0
    st.error(f"🚩 **En Fazla Tetkik İsteyen Hekim:** {dr_adi} | **Toplam:** {dr_total} Adet")
    st.info(f"📊 **Analiz:** **{dr_adi}** tarafından yapılan **{dr_total}** istemin; %{pan_yuzde:.1f} Panoramik, %{peri_yuzde:.1f} Periapikaldir.")
    c1, c2 = st.columns([2, 1])
    with c1:
        df_plot = hekim_analiz_filtered.melt(id_vars=C_HEKIM, value_vars=film_types, var_name='Tür', value_name='Adet')
        st.plotly_chart(px.bar(df_plot, x=C_HEKIM, y='Adet', color='Tür', barmode='group', title="Hekim Bazlı Tetkik Dağılımı", text_auto=True), use_container_width=True)
    with c2:
        st.dataframe(hekim_analiz_filtered[[C_HEKIM, C_PAN, C_PERI, 'TOPLAM_FILM']], hide_index=True, use_container_width=True)


with tab2:
    if C_BRANS:
        st.subheader("🏢 Branş Bazlı Dağılım ve Karakteristik Analizi")
        brans_data = df.groupby(C_BRANS)[film_types].sum().reset_index()
        
        # Akıllı Branş Yorumu
        top_brans = brans_data.sort_values(C_PAN, ascending=False).iloc[0]
        st.markdown(f"""
        > **🤖 Yönetici Notu:** Kurum genelinde Panoramik röntgen yükünün en ağır olduğu branş **{top_brans[C_BRANS]}** olarak tespit edilmiştir. 
        > Bu branş tek başına toplam Panoramik istemlerin **%{ (top_brans[C_PAN] / brans_data[C_PAN].sum() * 100):.1f}**'ini oluşturmaktadır.
        """)

        col_pie1, col_pie2 = st.columns(2)
        
        with col_pie1:
            fig_pan = px.pie(brans_data, values=C_PAN, names=C_BRANS, hole=0.4,
                             title="Branşlara Göre Panoramik Dağılımı",
                             color_discrete_sequence=px.colors.qualitative.Prism)
            fig_pan.update_traces(textinfo='percent+label', textposition='inside')
            st.plotly_chart(fig_pan, use_container_width=True)

        with col_pie2:
            fig_peri = px.pie(brans_data, values=C_PERI, names=C_BRANS, hole=0.4,
                              title="Branşlara Göre Periapikal Dağılımı",
                              color_discrete_sequence=px.colors.qualitative.Safe)
            fig_peri.update_traces(textinfo='percent+label', textposition='inside')
            st.plotly_chart(fig_peri, use_container_width=True)
        
        st.divider()
        st.plotly_chart(px.bar(brans_data, x=C_BRANS, y=film_types, title="Branş Bazlı Sayısal Karşılaştırma", barmode='group', text_auto=True), use_container_width=True)


with tab3:
    st.subheader("🔥 Hekim - Tetkik Türü Kullanım Yoğunluğu")
    h_height = max(450, num_dr * 35)
    fig_heat = px.imshow(hekim_analiz_filtered.set_index(C_HEKIM)[film_types], text_auto=True, color_continuous_scale='YlOrRd', height=h_height, aspect="auto")
    st.plotly_chart(fig_heat, use_container_width=True)


with tab4:
    st.subheader("📈 Tetkik İsteme Kararlılığı ve Anomali Analizi")
    total_avg = hekim_analiz_all['TOPLAM_FILM'].mean()
    anomali_dr = hekim_analiz_all[hekim_analiz_all['TOPLAM_FILM'] > (total_avg * 2)]
    
    st.markdown("### 🤖 Yönetici Karar Destek Özeti")
    c1, c2 = st.columns(2)
    with c1:
        st.info(f"**📊 Kurum Ortalaması:** Hekim başına düşen ortalama toplam tetkik **{total_avg:.1f}** adettir.")
    with c2:
        if not anomali_dr.empty:
            st.warning(f"**⚠️ Anomali:** {len(anomali_dr)} hekim kurum ortalamasının 2 katını aşmıştır. En yüksek: **{anomali_dr.iloc[0][C_HEKIM]}**")
        else:
            st.success("✅ İstem dağılımı tüm hekimler arasında dengeli.")

    st.divider()
    cp1, cp2 = st.columns([2, 1])
    with cp1:
        fig_box = px.box(hekim_analiz_all, y=[C_PAN, C_PERI], points="all", hover_data={C_HEKIM: True},
                         title="Hekim İstem Alışkanlıkları (İsim Detaylı)", color_discrete_sequence=['#636EFA', '#EF553B'])
        fig_box.update_traces(hovertemplate="<b>Hekim:</b> %{customdata[0]}<br><b>Sayı:</b> %{y}")
        st.plotly_chart(fig_box, use_container_width=True)
    with cp2:
        st.markdown("#### 🧐 Nasıl Okunur?\n* **Noktalar:** Her bir hekimi temsil eder.\n* **Üst Aykırılar:** Ortalamadan sapan ve tetkik maliyeti yüksek hekimlerdir.")

    st.divider()
    st.markdown("#### 🔄 Panoramik / Periapikal Tercih Dengesi")
    fig_scatter = px.scatter(hekim_analiz_all, x=C_PAN, y=C_PERI, size='TOPLAM_FILM', hover_name=C_HEKIM, 
                             color='TOPLAM_FILM', color_continuous_scale='Viridis')
    st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()
with st.expander("📊 Tüm Veri Matrisi (Sıralı)"):
    st.dataframe(hekim_analiz_all.sort_values('TOPLAM_FILM', ascending=False), hide_index=True)

utils.footer_ekle()