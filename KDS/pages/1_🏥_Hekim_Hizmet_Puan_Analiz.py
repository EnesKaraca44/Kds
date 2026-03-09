import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import utils
from database.doctor_point import load_doctor_points_data


st.set_page_config(page_title="Hekim Puan & Hizmet Analizi", page_icon="📊", layout="wide")

if not st.session_state.get("password_correct", False):
    st.warning("⚠️ Lütfen giriş yapın.")
    st.stop()

sd, ed = st.session_state.get('start_date'), st.session_state.get('end_date')


st.title("📊 Hekim Puan ve Hizmet Analiz Paneli")
utils.aktif_donem_goster()


@st.cache_data(show_spinner=False)
def get_processed_data(start_date, end_date):
    df_raw = load_doctor_points_data(start_date, end_date)
    if df_raw is None or df_raw.empty:
        return None
    
    temp_df = df_raw.copy()
    temp_df['TETKIK_TOPLAM_PUAN'] = pd.to_numeric(temp_df['TETKIK_TOPLAM_PUAN'], errors='coerce').fillna(0)
    temp_df['TETKIK_ADET'] = pd.to_numeric(temp_df['TETKIK_ADET'], errors='coerce').fillna(0)
    temp_df['TETKIK_BIRIM_UCRET'] = pd.to_numeric(temp_df['TETKIK_BIRIM_UCRET'], errors='coerce').fillna(0)
    temp_df['TOPLAM_GELIR'] = temp_df['TETKIK_ADET'] * temp_df['TETKIK_BIRIM_UCRET']
    return temp_df

with st.spinner("🔄 Veriler işleniyor..."):
    df = get_processed_data(sd, ed)

if df is None:
    st.info("ℹ️ Veri bulunamadı.")
    st.stop()


hekim_perf = df.groupby('TETKIK_DOKTOR_ADI').agg({
    'TETKIK_TARIHI': 'nunique',
    'HASTA_GELIS_NO': 'nunique',
    'TETKIK_TOPLAM_PUAN': 'sum',
    'TOPLAM_GELIR': 'sum'
}).reset_index()

hekim_perf.columns = ['Hekim', 'Calisma_Gun', 'Toplam_Hasta', 'Toplam_Puan', 'Toplam_Gelir']
hekim_perf['Hasta_Basi_Gelir'] = (hekim_perf['Toplam_Gelir'] / hekim_perf['Toplam_Hasta']).round(2)

total_puan = hekim_perf['Toplam_Puan'].sum()
total_gelir = hekim_perf['Toplam_Gelir'].sum()
avg_calisma_gun = hekim_perf['Calisma_Gun'].mean()
genel_cmi_gelir = total_gelir / hekim_perf['Toplam_Hasta'].sum()
kurum_hekim_gelir_ort = hekim_perf['Toplam_Gelir'].mean()


m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("🏆 Toplam Puan", utils.format_turkish_number(total_puan, 0))
m2.metric("💰 Toplam Gelir", f"₺ {utils.format_turkish_number(total_gelir, 2)}")
m3.metric("👥 Toplam Hasta", utils.format_turkish_number(hekim_perf['Toplam_Hasta'].sum(), 0))
m4.metric("👨‍⚕️ Aktif Hekim", len(hekim_perf))
m5.metric("📅 Ort. Çalışma Günü", f"{avg_calisma_gun:.1f} Gün")
m6.metric("📈 Kurum CMI (Ort.)", f"₺ {utils.format_turkish_number(genel_cmi_gelir, 2)}")

st.divider()

tabs = st.tabs([
    "🚀 Verimlilik & Gelir",
    "💊 Hizmet & Puan Analizi",
    "📈 Stratejik Trend & CMI",
    "📑 Detaylı Liste",
    "🎯 Akıllı Kıyas & Risk Analizi"
])


with tabs[0]:
    st.subheader("💰 Finansal Performans Sıralaması")
    sort_by = st.radio("Sıralama kriteri:", ["Toplam_Puan", "Toplam_Gelir", "Hasta_Basi_Gelir"], horizontal=True)
    top_n = st.slider("Hekim Sayısı:", 5, len(hekim_perf), 10)

    col_max, col_min = st.columns(2)
    # TL formatı için prefix kontrolü
    is_tl = "Gelir" in sort_by
    prefix = "₺ " if is_tl else ""

    with col_max:
        st.write(f"**En Yüksek {sort_by} Üretenler**")
        top_df = hekim_perf.nlargest(top_n, sort_by).sort_values(sort_by)
        fig_max = px.bar(top_df, x=sort_by, y='Hekim', orientation='h', 
                         color=sort_by, color_continuous_scale='Greens',
                         text_auto='.3s')
        fig_max.update_layout(xaxis_tickprefix=prefix)
        st.plotly_chart(fig_max, use_container_width=True)

    with col_min:
        st.write(f"**En Düşük {sort_by} Üretenler**")
        bottom_df = hekim_perf.nsmallest(top_n, sort_by).sort_values(sort_by, ascending=False)
        fig_min = px.bar(bottom_df, x=sort_by, y='Hekim', orientation='h', 
                         color=sort_by, color_continuous_scale='Reds',
                         text_auto='.3s')
        fig_min.update_layout(xaxis_tickprefix=prefix)
        st.plotly_chart(fig_min, use_container_width=True)


with tabs[1]:
    selected_hekim = st.selectbox("Hekim Seçin:", sorted(hekim_perf['Hekim'].unique()))
    h_data = hekim_perf[hekim_perf['Hekim'] == selected_hekim].iloc[0]
    
    fark_tutari = h_data['Toplam_Gelir'] - kurum_hekim_gelir_ort
    fark_yuzde = (fark_tutari / kurum_hekim_gelir_ort) * 100

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📅 Çalışma Günü", f"{h_data['Calisma_Gun']} Gün")
    c2.metric("🏆 Toplam Puan", utils.format_turkish_number(h_data['Toplam_Puan'], 0))
    c3.metric("💰 Toplam Gelir", f"₺ {utils.format_turkish_number(h_data['Toplam_Gelir'], 2)}")
    c4.metric("⚖️ Kurum Ort. Kıyas", f"₺ {utils.format_turkish_number(kurum_hekim_gelir_ort, 0)}", 
              delta=f"{fark_yuzde:.1f}%", help="Hekimin toplam geliri / Tüm hekimlerin gelir ortalaması")

   
    fig_comp = go.Figure()
    fig_comp.add_vline(x=kurum_hekim_gelir_ort, line_dash="dash", line_color="gray", annotation_text="Kurum Ortalaması")
    fig_comp.add_trace(go.Bar(
        x=[h_data['Toplam_Gelir']], y=[selected_hekim], orientation='h', 
        marker_color='#2ecc71' if fark_tutari > 0 else '#e74c3c',
        text=[f"₺ {utils.format_turkish_number(h_data['Toplam_Gelir'], 0)}"],
        textposition='inside'
    ))
    fig_comp.update_layout(height=180, margin=dict(l=0, r=0, t=30, b=0), xaxis_tickprefix="₺ ")
    st.plotly_chart(fig_comp, use_container_width=True)

    st.subheader(f"📑 {selected_hekim} - Hizmet Dağılımı")
    h_services = df[df['TETKIK_DOKTOR_ADI'] == selected_hekim].groupby('TETKIK_ADI').agg({
        'TETKIK_ADET': 'sum', 'TETKIK_TOPLAM_PUAN': 'sum', 'TOPLAM_GELIR': 'sum'
    }).reset_index().sort_values('TOPLAM_GELIR', ascending=False)
    
 
    st.dataframe(
        h_services.style.format({
            'TETKIK_TOPLAM_PUAN': '{:,.0f}', 
            'TOPLAM_GELIR': '₺ {:,.2f}',
            'TETKIK_ADET': '{:,.0f}'
        }), 
        use_container_width=True, hide_index=True
    )


with tabs[2]:
    col_left, col_right = st.columns(2)
    with col_left:
        st.write("**Gelir Dominansı (Pareto)**")
        pareto_df = hekim_perf.sort_values("Toplam_Gelir", ascending=False).copy()
        pareto_df['Kumulatif_Yuzde'] = 100 * pareto_df['Toplam_Gelir'].cumsum() / total_gelir
        fig_p = px.bar(pareto_df, x='Hekim', y='Toplam_Gelir', text_auto='.2s')
        fig_p.add_scatter(x=pareto_df['Hekim'], y=pareto_df['Kumulatif_Yuzde'], name='Kümülatif %', yaxis='y2', line=dict(color="#f39c12"))
        fig_p.update_layout(yaxis2=dict(anchor='x', overlaying='y', side='right', range=[0, 105]), yaxis_tickprefix="₺ ")
        st.plotly_chart(fig_p, use_container_width=True)
        
    with col_right:
        st.write("**Hasta Sayısı vs Hasta Başı Gelir (CMI)**")
        outlier_fix = st.checkbox("Aykırı Değerleri Sınırla", value=True)
        y_max = hekim_perf['Hasta_Basi_Gelir'].quantile(0.90) * 1.5 if outlier_fix else hekim_perf['Hasta_Basi_Gelir'].max()
        fig_cmi = px.scatter(hekim_perf, x="Toplam_Hasta", y="Hasta_Basi_Gelir", size="Toplam_Puan", 
                             color="Hasta_Basi_Gelir", hover_name="Hekim", text="Hekim", color_continuous_scale='Viridis')
        fig_cmi.update_traces(textposition='top center')
        fig_cmi.update_yaxes(range=[0, y_max], tickprefix="₺ ")
        fig_cmi.add_hline(y=genel_cmi_gelir, line_dash="dash", line_color="red", annotation_text="Kurum CMI Ortalaması")
        st.plotly_chart(fig_cmi, use_container_width=True)


with tabs[3]:
    detay_df = df[['TETKIK_DOKTOR_ADI', 'HASTA_ADI_SOYADI', 'TETKIK_ADI', 'TETKIK_ADET', 'TETKIK_TOPLAM_PUAN', 'TOPLAM_GELIR', 'TETKIK_TARIHI']].copy()
    detay_df['TOPLAM_GELIR'] = detay_df['TOPLAM_GELIR'].apply(lambda x: f"₺ {x:,.2f}")
    detay_df['TETKIK_TOPLAM_PUAN'] = detay_df['TETKIK_TOPLAM_PUAN'].astype(int)
    st.dataframe(detay_df, use_container_width=True, hide_index=True)


with tabs[4]:
    st.subheader("🛡️ Risk ve Potansiyel Skorlama")
    
    def get_performance_tags(row):
        tags = []
        if row['Hasta_Basi_Gelir'] < (genel_cmi_gelir * 0.75): tags.append("⚠️ Düşük CMI Riski")
        if row['Toplam_Hasta'] > hekim_perf['Toplam_Hasta'].median() and row['Toplam_Puan'] < hekim_perf['Toplam_Puan'].median():
            tags.append("⚠️ Operasyonel Yük Yüksek / Verim Düşük")
        if row['Hasta_Basi_Gelir'] > (genel_cmi_gelir * 1.5): tags.append("⭐ Premium Hizmet Üretimi")
        if row['Calisma_Gun'] < avg_calisma_gun and row['Toplam_Gelir'] > kurum_hekim_gelir_ort: tags.append("⚡ Yüksek Günlük Verimlilik")
        return " | ".join(tags) if tags else "✅ Dengeli"

    risk_df = hekim_perf.copy()
    risk_df['Durum_Analizi'] = risk_df.apply(get_performance_tags, axis=1)
    
  
    st.dataframe(
        risk_df[['Hekim', 'Toplam_Gelir', 'Hasta_Basi_Gelir', 'Durum_Analizi']]
        .sort_values('Toplam_Gelir', ascending=False)
        .style.format({'Toplam_Gelir': '₺ {:,.2f}', 'Hasta_Basi_Gelir': '₺ {:,.2f}'}),
        use_container_width=True, hide_index=True
    )

    st.divider()
    st.subheader("🔬 Akran Grubu (Peer Group) Karşılaştırması")
    target_h = st.selectbox("Analiz Edilecek Hekim:", sorted(hekim_perf['Hekim'].unique()), key="peer_final")
    t_data = hekim_perf[hekim_perf['Hekim'] == target_h].iloc[0]
    
 
    peers = hekim_perf[(hekim_perf['Hekim'] != target_h) & 
                       (hekim_perf['Calisma_Gun'].between(t_data['Calisma_Gun']*0.75, t_data['Calisma_Gun']*1.25)) &
                       (hekim_perf['Toplam_Hasta'].between(t_data['Toplam_Hasta']*0.75, t_data['Toplam_Hasta']*1.25))]

    if not peers.empty:
        comp_df = pd.concat([pd.DataFrame([t_data]), peers])
        fig_peers = px.bar(comp_df, x='Hekim', y='Toplam_Gelir', color='Hasta_Basi_Gelir', 
                           title="Benzer Yoğunluktaki Hekimler Finansal Kıyas",
                           color_continuous_scale='Portland')
        fig_peers.update_layout(yaxis_tickprefix="₺ ")
        st.plotly_chart(fig_peers, use_container_width=True)
        
        st.write("**Karşılaştırmalı Veri Tablosu:**")
        st.table(comp_df[['Hekim', 'Calisma_Gun', 'Toplam_Hasta', 'Hasta_Basi_Gelir', 'Toplam_Gelir']]
                 .rename(columns={'Hasta_Basi_Gelir': 'Hasta B. Gelir (₺)', 'Toplam_Gelir': 'Toplam Gelir (₺)'}))
    else:
        st.info("ℹ️ Bu hekimin çalışma yoğunluğuna benzer bir akran grubu bulunamadı.")

utils.footer_ekle()