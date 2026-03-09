import streamlit as st
import pandas as pd
import plotly.express as px
import utils 
from database.referral_loaders import load_referral_data


st.set_page_config(page_title="Hekim Sevk Analizi", page_icon="🩺", layout="wide")

if not st.session_state.get("password_correct", False):
    st.warning("🔒 Lütfen Ana Sayfa'dan giriş yapın.")
    st.stop()

start_date = st.session_state.get('start_date')
end_date = st.session_state.get('end_date')


df_referrals = load_referral_data(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))

if df_referrals is None or df_referrals.empty:
    st.info("ℹ️ Seçilen dönemde veri bulunamadı.")
    st.stop()


COL_EDEN_DR = 'Sevk_Eden_Doktor_Ad'
COL_KABUL_DR = 'Sevk_Kabul_Doktor_Ad'
COL_EDEN_SRV = 'Sevk_Eden_Srv_Ad'
COL_KABUL_SRV = 'Sevk_Kabul_Srv_Ad'
COL_HASTA = 'TOPLAM_HASTA' 
COL_SEVK = 'TOPLAM_SEVK'


oran_df = df_referrals.groupby(COL_EDEN_DR).agg({
    COL_HASTA: 'max', 
    COL_SEVK: 'sum'
}).reset_index()
oran_df['ORAN'] = (oran_df[COL_SEVK] / oran_df[COL_HASTA] * 100).fillna(0)

total_h = oran_df[COL_HASTA].sum()
total_s = df_referrals[COL_SEVK].sum()
genel_ort = (total_s / total_h * 100) if total_h > 0 else 0


st.title("🩺 Hekim Sevk & Akıllı Karar Destek")
utils.aktif_donem_goster()

m1, m2, m3, m4 = st.columns(4)
m1.metric("👥 Toplam Hasta", utils.format_turkish_number(total_h, 0))
m2.metric("📤 Toplam Sevk", utils.format_turkish_number(total_s, 0))
m3.metric("🎯 Genel Sevk Oranı", f"%{genel_ort:.1f}")
m4.metric("👨‍⚕️ Aktif Hekim Sayısı", len(oran_df))

st.divider()


tabs = st.tabs([
    "📈 Genel Trafik", 
    "🎯 Sevk Oranları", 
    "🏢 Branş Analizi",
    "🤝 Hekim-Branş Eşleşmesi", 
    "🔗 Eşleşmeler", 
    "🔍 Hekim Detaylı Arama", 
    "📄 Ham Veri"
])


with tabs[0]:
    c1, c2 = st.columns(2)
    top_n = st.slider("Hekim Sayısı:", 5, 30, 10)
    with c1:
        st.subheader("En Çok Sevk Yapanlar")
        g1 = df_referrals.groupby(COL_EDEN_DR)[COL_SEVK].sum().nlargest(top_n).reset_index()
        st.plotly_chart(px.bar(g1, x=COL_SEVK, y=COL_EDEN_DR, orientation='h', color_continuous_scale='Reds'), use_container_width=True)
    with c2:
        st.subheader("En Çok Sevk Kabul Edenler")
        g2 = df_referrals.groupby(COL_KABUL_DR)[COL_SEVK].sum().nlargest(top_n).reset_index()
        st.plotly_chart(px.bar(g2, x=COL_SEVK, y=COL_KABUL_DR, orientation='h', color_continuous_scale='Blues'), use_container_width=True)


with tabs[1]:
    st.subheader("🎯 Hekim Bazlı Sevk Verimliliği")
    st.plotly_chart(px.scatter(oran_df, x=COL_HASTA, y=COL_SEVK, size='ORAN', color='ORAN', hover_name=COL_EDEN_DR), use_container_width=True)
    st.dataframe(oran_df.sort_values('ORAN', ascending=False), use_container_width=True, hide_index=True)


with tabs[2]:
    st.subheader("🏢 Servisler Arası Sevk Trafiği")
    brans_flow = df_referrals.groupby([COL_EDEN_SRV, COL_KABUL_SRV])[COL_SEVK].sum().reset_index()
    
    col_akilli, col_grafik = st.columns([1, 2])
    with col_akilli:
        st.markdown("### 🤖 Branş Akıllı Analiz")
        top_k_br = brans_flow.groupby(COL_KABUL_SRV)[COL_SEVK].sum().idxmax()
        top_e_br = brans_flow.groupby(COL_EDEN_SRV)[COL_SEVK].sum().idxmax()
        
        st.info(f"""
        **📍 Stratejik Özet:**
        * En çok sevk **{top_e_br}** servisinden çıkmaktadır.
        * Sevklerin ana toplama merkezi **{top_k_br}** branşıdır.
        """)
        st.write("📋 **En Yoğun 10 Akış**")
        st.dataframe(brans_flow.nlargest(10, COL_SEVK).rename(columns={COL_EDEN_SRV:'Kaynak', COL_KABUL_SRV:'Hedef', COL_SEVK:'Adet'}), hide_index=True)

    with col_grafik:
        fig_brans = px.bar(brans_flow.nlargest(15, COL_SEVK), x=COL_EDEN_SRV, y=COL_SEVK, color=COL_KABUL_SRV,
                           title="Branş Bazlı Sevk Dağılımı", text_auto=True)
        st.plotly_chart(fig_brans, use_container_width=True)


with tabs[3]:
    st.subheader("🤝 Hekimlerin Branş Tercih Analizi")
    st.markdown("Hekimlerin en çok hangi branşlara (servislere) sevk yaptığını analiz edin.")
    
    
    dr_brans_map = df_referrals.groupby([COL_EDEN_DR, COL_KABUL_SRV])[COL_SEVK].sum().reset_index()
    
   
    all_drs = sorted(dr_brans_map[COL_EDEN_DR].unique())
    selected_drs = st.multiselect("Analiz edilecek hekimleri seçin:", all_drs, default=all_drs[:10])
    
    if selected_drs:
        filtered_map = dr_brans_map[dr_brans_map[COL_EDEN_DR].isin(selected_drs)]
        
        col_m1, col_m2 = st.columns([2, 1])
        with col_m1:
            fig_map = px.bar(
                filtered_map, 
                x=COL_EDEN_DR, 
                y=COL_SEVK, 
                color=COL_KABUL_SRV,
                title="Hekimlerin Hedef Branş Dağılımı",
                text_auto=True
            )
            st.plotly_chart(fig_map, use_container_width=True)
            
        with col_m2:
            st.write("📋 **Hekimlerin 'Favori' Sevk Branşları**")
            
            fav_brans = filtered_map.sort_values([COL_EDEN_DR, COL_SEVK], ascending=[True, False]).groupby(COL_EDEN_DR).head(1)
            st.dataframe(
                fav_brans.rename(columns={COL_EDEN_DR: 'Hekim', COL_KABUL_SRV: 'En Çok Sevk Edilen Branş', COL_SEVK: 'Adet'}),
                hide_index=True, use_container_width=True
            )
    else:
        st.warning("Lütfen yukarıdan en az bir hekim seçiniz.")


with tabs[4]:
    st.subheader("🔗 Kritik Konsültasyon Kanalları")
    df_pair = df_referrals.dropna(subset=[COL_EDEN_DR, COL_KABUL_DR])
    df_pair = df_pair.groupby([COL_EDEN_DR, COL_KABUL_DR])[COL_SEVK].sum().reset_index()
    df_pair['KANAL'] = df_pair[COL_EDEN_DR] + " ➜ " + df_pair[COL_KABUL_DR]
    st.plotly_chart(px.bar(df_pair.nlargest(15, COL_SEVK), x=COL_SEVK, y='KANAL', orientation='h', text_auto=True), use_container_width=True)


with tabs[5]:
    st.subheader("🔍 Hekim Bazlı Sevk Akış Analizi")
    referring_list = sorted(df_referrals[COL_EDEN_DR].dropna().unique())
    selected_dr = st.selectbox("Sevk Analizi İçin Hekim Seçiniz:", referring_list, key="detail_dr_select")
    
    dr_data = df_referrals[df_referrals[COL_EDEN_DR] == selected_dr]
    out_refs = dr_data.groupby(COL_KABUL_DR)[COL_SEVK].sum().reset_index()
    
    if not out_refs.empty:
        total_out = out_refs[COL_SEVK].sum()
        hastasi = dr_data[COL_HASTA].max()
        orani = (total_out / hastasi * 100) if hastasi > 0 else 0

        ck1, ck2, ck3 = st.columns(3)
        ck1.metric(label="Toplam Hasta", value=f"{hastasi:,.0f}".replace(",", "."))
        ck2.metric(label="Toplam Sevk Sayısı", value=f"{total_out:,.0f}".replace(",", "."))
        ck3.metric(label="Sevk Oranı", value=f"%{orani:.1f}", 
                   delta=f"{orani - genel_ort:.1f}% (Genel Fark)", delta_color="inverse")

        st.divider()
        col_chart, col_table = st.columns([2, 1])
        with col_chart:
            st.write(f"📊 **{selected_dr}** - Hekim Sevk Dağılımı")
            fig_out = px.pie(out_refs, values=COL_SEVK, names=COL_KABUL_DR, hole=0.4)
            st.plotly_chart(fig_out, use_container_width=True)
            
            st.write("🏢 **Hekimin Tercih Ettiği Branşlar**")
            dr_brans = dr_data.groupby(COL_KABUL_SRV)[COL_SEVK].sum().reset_index()
            st.plotly_chart(px.bar(dr_brans, x=COL_SEVK, y=COL_KABUL_SRV, orientation='h', color=COL_SEVK), use_container_width=True)
            
        with col_table:
            st.write("📋 **Kabul Eden Hekimler**")
            st.dataframe(out_refs.sort_values(by=COL_SEVK, ascending=False).rename(columns={COL_KABUL_DR: 'Hekim', COL_SEVK: 'Adet'}), hide_index=True)
    else:
        st.warning(f"Seçilen hekime ({selected_dr}) ait sevk kaydı bulunamadı.")


with tabs[6]:
    st.dataframe(df_referrals, use_container_width=True)

utils.footer_ekle()