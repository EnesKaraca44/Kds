import streamlit as st
import pandas as pd
import plotly.express as px
import utils
from database.medical_loaders import load_treatment_group_performance

st.set_page_config(page_title="Tedavi Analizi", page_icon="🩺", layout="wide")

st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1a2744 0%, #0d1b3e 100%);
        border: 1px solid #2d4a8a;
        border-radius: 12px;
        padding: 18px 22px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .metric-label {
        color: #8fa8d0;
        font-size: 0.82rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .metric-value {
        color: #e8f0fe;
        font-size: 1.75rem;
        font-weight: 700;
        line-height: 1.2;
    }
    .date-pill {
        display: inline-block;
        background: #1565C0;
        color: #e3f2fd;
        padding: 5px 18px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        margin-bottom: 18px;
    }
    .section-title {
        color: #cdd9f5;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .insight-row {
        border-radius: 8px;
        padding: 10px 16px;
        margin-bottom: 8px;
        font-size: 0.9rem;
        color: #e0e8ff;
    }
</style>
""", unsafe_allow_html=True)

if not st.session_state.get("password_correct", False):
    st.warning("🔒 Lütfen Ana Sayfa'dan giriş yapın.")
    st.stop()

sd = st.session_state.get("start_date")
ed = st.session_state.get("end_date")
if not sd or not ed:
    st.error("📅 Lütfen Ana Sayfa'dan bir tarih aralığı seçin.")
    st.stop()

df_raw = load_treatment_group_performance(sd.strftime("%Y-%m-%d"), ed.strftime("%Y-%m-%d"))
if df_raw.empty:
    st.warning("🩺 Seçilen dönem için tedavi grubu verisi bulunamadı.")
    st.stop()

df = df_raw.copy()
df.columns = [c.upper().strip() for c in df.columns]

group_col   = "TEDAVI_GRUBU_ADI"
patient_col = "HASTA_KODU"
revenue_col = "TETKIK_TOPLAM_UCRET"
count_col   = "TOPLAM_ADET"

df = df[~df[group_col].isin(["BELİRTİLMEMİŞ", "", None])]

# ── Header ──────────────────────────────────────────────────────────────────
st.title("🩺 Tedavi Grupları Analizi")

st.markdown(
    f"<div class='date-pill'>📅 {sd.strftime('%d.%m.%Y')} – {ed.strftime('%d.%m.%Y')}</div>",
    unsafe_allow_html=True,
)

# ── KPI Cards ────────────────────────────────────────────────────────────────
grup_sayisi = df[group_col].nunique()
tekil_hasta = df[patient_col].nunique()
islem_hacmi = int(df[count_col].sum())
toplam_ciro = float(df[revenue_col].sum())

k1, k2, k3, k4 = st.columns(4)
for col, label, value in [
    (k1, "Grup Sayısı",       str(grup_sayisi)),
    (k2, "Tekil Hasta",       utils.format_turkish_number(tekil_hasta, 0)),
    (k3, "İşlem Hacmi",       utils.format_turkish_number(islem_hacmi, 0)),
    (k4, "Toplam Ciro (₺)",   utils.format_turkish_number(toplam_ciro, 2)),
]:
    col.markdown(
        f"""<div class='metric-card'>
            <div class='metric-label'>{label}</div>
            <div class='metric-value'>{value}</div>
        </div>""",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

# ── Sidebar ──────────────────────────────────────────────────────────────────
top_n = st.sidebar.slider("Gösterilecek Grup Sayısı", 5, 50, 15, 5)

# ── Summary aggregation ──────────────────────────────────────────────────────
summary = (
    df.groupby(group_col, as_index=False)
    .agg({patient_col: "nunique", count_col: "sum", revenue_col: "sum"})
    .rename(columns={
        patient_col: "HASTA_SAYISI",
        count_col:   "ISLEM_ADETI",
        revenue_col: "TOPLAM_CIRO",
    })
)
summary["ISLEM_BASI_GELIR"] = summary["TOPLAM_CIRO"] / summary["ISLEM_ADETI"]

CHART_TEMPLATE = "plotly_dark"
CHART_HEIGHT   = 480

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["🔥 Performans Kıyaslama", "🔍 Grup Detayları"])

with tab1:
    c_gelir, c_islem = st.columns(2)

    # ── Gelire Göre Top N ────────────────────────────────────────────────────
    with c_gelir:
        st.markdown(
            f"<p class='section-title'>💰 Gelire Göre Top {top_n}</p>",
            unsafe_allow_html=True,
        )
        top_gelir = summary.nlargest(top_n, "TOPLAM_CIRO").sort_values("TOPLAM_CIRO")
        fig_g = px.bar(
            top_gelir, x="TOPLAM_CIRO", y=group_col, orientation="h",
            color="TOPLAM_CIRO", color_continuous_scale="Blues",
            template=CHART_TEMPLATE, height=CHART_HEIGHT,
            labels={"TOPLAM_CIRO": "Toplam Ciro (₺)", group_col: ""},
        )
        fig_g.update_traces(
            texttemplate="%{x:.3s}",
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Ciro: %{x:,.0f} ₺<extra></extra>",
        )
        fig_g.update_layout(
            showlegend=False,
            margin=dict(l=10, r=40, t=20, b=20),
            xaxis=dict(showgrid=False, tickformat=".3s"),
            yaxis=dict(tickfont=dict(size=10)),
            coloraxis_colorbar=dict(title="Ciro", tickformat=".2s"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_g, use_container_width=True)

    # ── İşleme Göre Top N ───────────────────────────────────────────────────
    with c_islem:
        st.markdown(
            f"<p class='section-title'>⚕️ İşleme Göre Top {top_n}</p>",
            unsafe_allow_html=True,
        )
        top_islem = summary.nlargest(top_n, "ISLEM_ADETI").sort_values("ISLEM_ADETI")
        fig_i = px.bar(
            top_islem, x="ISLEM_ADETI", y=group_col, orientation="h",
            color="ISLEM_ADETI", color_continuous_scale="Greens",
            template=CHART_TEMPLATE, height=CHART_HEIGHT,
            labels={"ISLEM_ADETI": "İşlem Adedi", group_col: ""},
        )
        fig_i.update_traces(
            texttemplate="%{x:.3s}",
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>İşlem: %{x:,.0f}<extra></extra>",
        )
        fig_i.update_layout(
            showlegend=False,
            margin=dict(l=10, r=40, t=20, b=20),
            xaxis=dict(showgrid=False, tickformat=".3s"),
            yaxis=dict(tickfont=dict(size=10)),
            coloraxis_colorbar=dict(title="Adet", tickformat=".2s"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_i, use_container_width=True)

    st.markdown("---")

    # ── Verimlilik Scatter ───────────────────────────────────────────────────
    st.markdown(
        "<p class='section-title'>💡 Verimlilik Analizi (Birim Başı Gelir)</p>",
        unsafe_allow_html=True,
    )
    scatter_df = summary.nlargest(top_n, "ISLEM_BASI_GELIR").copy()
    scatter_df["ISLEM_BASI_GELIR_LBL"] = scatter_df["ISLEM_BASI_GELIR"].apply(
        lambda v: utils.format_turkish_number(v, 2) + " ₺"
    )
    fig_s = px.scatter(
        scatter_df,
        x="ISLEM_ADETI", y="TOPLAM_CIRO",
        size="ISLEM_BASI_GELIR", color=group_col,
        hover_name=group_col,
        hover_data={
            "ISLEM_ADETI": True,
            "TOPLAM_CIRO": True,
            "ISLEM_BASI_GELIR_LBL": True,
            group_col: False,
        },
        template=CHART_TEMPLATE, height=420,
        labels={
            "ISLEM_ADETI": "İşlem Adedi",
            "TOPLAM_CIRO": "Toplam Ciro (₺)",
            "ISLEM_BASI_GELIR_LBL": "Birim Başı Gelir",
        },
    )
    fig_s.update_layout(
        margin=dict(l=10, r=10, t=20, b=20),
        xaxis=dict(tickformat=".3s"),
        yaxis=dict(tickformat=".3s"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            orientation="v", x=1.01, y=1,
            font=dict(size=10),
            bgcolor="rgba(13,27,62,0.8)",
            bordercolor="#2d4a8a",
            borderwidth=1,
        ),
    )
    st.plotly_chart(fig_s, use_container_width=True)

# ── Grup Detayları ───────────────────────────────────────────────────────────
with tab2:
    sel_group = st.selectbox(
        "Detaylı incelemek için bir grup seçin:",
        sorted(df[group_col].unique()),
    )
    if sel_group:
        g_df = df[df[group_col] == sel_group]
        detay = (
            g_df.groupby("TETKIK_ADI")
            .agg({count_col: "sum", revenue_col: "sum"})
            .sort_values(count_col, ascending=False)
            .reset_index()
        )
        detay.columns = ["Tetkik Adı", "İşlem Adedi", "Toplam Ciro (₺)"]
        st.dataframe(
            detay.style.format({"İşlem Adedi": "{:,.0f}", "Toplam Ciro (₺)": "{:,.2f}"}),
            use_container_width=True,
            hide_index=True,
        )

# ── Sistem Analizi ───────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.subheader("🎯 Sistem Analizi")
INSIGHT_COLORS = ["#1565C0", "#0277BD", "#00695C", "#4527A0"]
for idx, insight in enumerate(
    utils.generate_smart_insights(summary, group_col, "TOPLAM_CIRO", "ISLEM_ADETI")
):
    color = INSIGHT_COLORS[idx % len(INSIGHT_COLORS)]
    st.markdown(
        f"<div class='insight-row' style='background:{color}20; border-left:4px solid {color};'>"
        f"{insight}</div>",
        unsafe_allow_html=True,
    )

utils.footer_ekle()
