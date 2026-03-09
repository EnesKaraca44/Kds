from flask import Blueprint, render_template, request
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required  # noqa: E402
from database.denture_loaders import load_prosthetic_performance_data  # noqa: E402
from routes.dashboard import get_date_range  # noqa: E402

protez_bp = Blueprint("protez", __name__)


def _find_column(candidates, df_cols):
    for c in candidates:
        key = c.upper()
        if key in df_cols:
            return key
    return None


@protez_bp.route("/protez")
@login_required
def protez():
    sd, ed = get_date_range()
    df_raw = load_prosthetic_performance_data(sd, ed)

    if df_raw is None or df_raw.empty:
        return render_template("protez.html", start_date=sd, end_date=ed, no_data=True)

    df = df_raw.copy()
    df.columns = [str(c).upper().strip().replace(" ", "_") for c in df.columns]

    C_HEKIM = _find_column(["HEKIM_ADI", "HEKIMAD", "DKTAD", "DOKTOR_ADI"], df.columns)
    C_PLAN = _find_column(
        ["PLANLANANTESLIMSURESI", "PLAN_SURE", "HEDEF_GUN"],
        df.columns,
    )
    C_GERCEK = _find_column(
        ["ORTALAMA_TESLIM_SURESI", "ORTALAMA_TESLIM_SÜRESI", "TESLIM_SURE_GUN"],
        df.columns,
    )
    C_SUT = _find_column(["SUT_ADI", "PROTEZADI", "ACIKLAMA", "ISLEM_ADI"], df.columns)
    C_HASTA_KOD = _find_column(["HASTA_KODU", "HASTA_KOD"], df.columns)
    C_HASTA_AD = _find_column(["HASTA_ADI", "HASTA_AD"], df.columns)
    C_TEDAVI_TARIH = _find_column(["TEDAVI_TARIHI", "BITIS_TARIHI"], df.columns)
    C_AY = _find_column(["AYADI", "AY"], df.columns)

    if not C_HEKIM or not C_PLAN or not C_GERCEK:
        return render_template("protez.html", start_date=sd, end_date=ed, no_data=True)

    # Temel metrik kolonları
    df["PLAN"] = pd.to_numeric(df[C_PLAN], errors="coerce").fillna(0).round(0).astype(int)
    df["GERCEK"] = pd.to_numeric(df[C_GERCEK], errors="coerce").fillna(0).round(1)
    df["GECIKME_GUN"] = (df["GERCEK"] - df["PLAN"]).round(1)
    df["GECIKEN"] = df["GECIKME_GUN"] > 0

    # Analiz ayarları (kritik gün eşiği ve gösterilecek hekim sayısı)
    try:
        kritik_limit = int(request.args.get("kritik", 30))
    except (TypeError, ValueError):
        kritik_limit = 30
    kritik_limit = max(1, min(365, kritik_limit))

    try:
        kritik_hekim_sayisi = int(request.args.get("k_hekim", 10))
    except (TypeError, ValueError):
        kritik_hekim_sayisi = 10
    kritik_hekim_sayisi = max(3, min(50, kritik_hekim_sayisi))

    # Genel metrikler
    vaka_sayisi = int(len(df))
    geciken_vaka = int(df["GECIKEN"].sum())
    gecikme_orani = (geciken_vaka / vaka_sayisi * 100.0) if vaka_sayisi > 0 else 0.0
    ort_teslim = float(df["GERCEK"].mean()) if vaka_sayisi > 0 else 0.0

    # ---- Sekme 1: Genel Performans (hedef vs gerçek + en çok geciken işlemler) ----
    top_hekimler = (
        df.groupby(C_HEKIM)["GECIKEN"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .index.tolist()
    )
    df_top = df[df[C_HEKIM].isin(top_hekimler)].copy()

    comp_df = (
        df_top.groupby(C_HEKIM)[["PLAN", "GERCEK"]]
        .mean()
        .round(1)
        .reset_index()
        .sort_values("GERCEK", ascending=False)
    )

    fig_hekim = go.Figure()
    fig_hekim.add_trace(
        go.Bar(
            x=comp_df[C_HEKIM],
            y=comp_df["PLAN"],
            name="Hedef",
            marker_color="#2563eb",
        )
    )
    fig_hekim.add_trace(
        go.Bar(
            x=comp_df[C_HEKIM],
            y=comp_df["GERCEK"],
            name="Gerçek",
            marker_color="#f97316",
        )
    )
    fig_hekim.update_layout(
        barmode="group",
        template="plotly_dark",
        height=420,
        margin=dict(l=10, r=10, t=10, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title="", tickangle=-45),
        yaxis=dict(title="Gün"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    if C_SUT:
        sut_risk = (
            df[df["GECIKEN"]]
            .groupby(C_SUT)["GECIKME_GUN"]
            .mean()
            .round(1)
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )
        fig_sut = px.bar(
            sut_risk.sort_values("GECIKME_GUN"),
            x="GECIKME_GUN",
            y=C_SUT,
            orientation="h",
            color="GECIKME_GUN",
            color_continuous_scale="Reds",
            labels={"GECIKME_GUN": "Gecikme (Gün)", C_SUT: ""},
        )
        fig_sut.update_layout(
            template="plotly_dark",
            height=420,
            margin=dict(l=10, r=20, t=10, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            coloraxis_showscale=True,
        )
    else:
        fig_sut = go.Figure()
        fig_sut.update_layout(
            template="plotly_dark",
            height=420,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

    # ---- Sekme 2: Geciken Hekim Listesi (kritik sınır üstü) ----
    df_kritik = df[df["GECIKME_GUN"] > kritik_limit].copy()
    kritik_summary = (
        df_kritik.groupby(C_HEKIM)
        .agg(
            vaka_sayisi=("GECIKME_GUN", "size"),
            ort_gecikme=("GECIKME_GUN", "mean"),
            toplam_gecikme=("GECIKME_GUN", "sum"),
        )
        .reset_index()
        .sort_values("ort_gecikme", ascending=False)
        .head(kritik_hekim_sayisi)
    )
    kritik_summary["ort_gecikme"] = kritik_summary["ort_gecikme"].round(1)
    kritik_summary["toplam_gecikme"] = kritik_summary["toplam_gecikme"].round(1)
    kritik_rows = kritik_summary.to_dict(orient="records")

    # ---- Sekme 3: Hasta Detayları ----
    hekim_list = (
        df.groupby(C_HEKIM)["GECIKME_GUN"]
        .mean()
        .reset_index()
        .sort_values("GECIKME_GUN", ascending=False)[C_HEKIM]
        .tolist()
    )

    selected_hekim = request.args.get("hekim") or (hekim_list[0] if hekim_list else "")
    only_delayed = request.args.get("only_delayed") == "on"

    detay_df = df[df[C_HEKIM] == selected_hekim].copy() if selected_hekim else df.copy()
    if only_delayed:
        detay_df = detay_df[detay_df["GECIKEN"]].copy()

    if C_HASTA_KOD and C_HASTA_AD:
        detay_cols = [C_HASTA_KOD, C_HASTA_AD]
    else:
        detay_cols = []
    if C_SUT:
        detay_cols.append(C_SUT)
    detay_cols += ["PLAN", "GERCEK", "GECIKME_GUN"]
    detay_cols = [c for c in detay_cols if c in detay_df.columns]

    detay_table = detay_df[detay_cols].head(500).to_dict(orient="records")

    # ---- Sekme 4: Trend Analizi (aylık ortalama gecikme) ----
    trend_df = df.copy()
    if C_TEDAVI_TARIH:
        trend_df["Tarih"] = pd.to_datetime(trend_df[C_TEDAVI_TARIH], dayfirst=True, errors="coerce")
        trend_df = trend_df.dropna(subset=["Tarih"])
        trend_df["AY"] = trend_df["Tarih"].dt.to_period("M").dt.to_timestamp()
        trend_group = (
            trend_df.groupby("AY")["GECIKME_GUN"].mean().round(1).reset_index()
        )
        x_col = "AY"
    elif C_AY:
        # Ay isimlerinden basit sıralama
        ay_order = [
            "OCAK",
            "ŞUBAT",
            "MART",
            "NİSAN",
            "MAYIS",
            "HAZİRAN",
            "TEMMUZ",
            "AĞUSTOS",
            "EYLÜL",
            "EKİM",
            "KASIM",
            "ARALIK",
        ]
        trend_df["AY"] = trend_df[C_AY].str.upper()
        trend_df["AY"] = pd.Categorical(trend_df["AY"], categories=ay_order, ordered=True)
        trend_group = (
            trend_df.groupby("AY")["GECIKME_GUN"].mean().round(1).reset_index()
        )
        x_col = "AY"
    else:
        trend_group = pd.DataFrame(columns=["X", "GECIKME_GUN"])
        x_col = "X"

    fig_trend = px.line(
        trend_group,
        x=x_col,
        y="GECIKME_GUN",
        markers=True,
        labels={"GECIKME_GUN": "Ortalama Gecikme (Gün)", x_col: "Dönem"},
    )
    fig_trend.update_traces(line=dict(color="#60a5fa", width=2))
    fig_trend.update_layout(
        template="plotly_dark",
        height=420,
        margin=dict(l=10, r=20, t=10, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    # Stratejik analiz notları (basit kurallara dayalı)
    insights = []
    if ort_teslim > 14:
        insights.append(
            "Operasyonel verimlilik uyarısı: Ortalama teslim süresi 14 günü aşmış görünüyor."
        )
    else:
        insights.append(
            "Operasyonel verimlilik iyi seviyede: Ortalama teslim süresi 14 günün altında."
        )
    if gecikme_orani > 10:
        insights.append(
            f"Gecikme oranı %{gecikme_orani:.1f}; kritik hekim ve işlem grupları için aksiyon önerilir."
        )
    if kritik_summary.shape[0] > 0:
        top_row = kritik_summary.iloc[0]
        insights.append(
            f"En riskli hekim: {top_row[C_HEKIM]} (kritik sınırı aşan {int(top_row['vaka_sayisi'])} vaka)."
        )

    cfg = {"responsive": True}
    charts = {
        "fig_hekim": fig_hekim.to_html(full_html=False, include_plotlyjs=False, config=cfg),
        "fig_sut": fig_sut.to_html(full_html=False, include_plotlyjs=False, config=cfg),
        "fig_trend": fig_trend.to_html(full_html=False, include_plotlyjs=False, config=cfg),
    }

    return render_template(
        "protez.html",
        start_date=sd,
        end_date=ed,
        no_data=False,
        vaka_sayisi=vaka_sayisi,
        geciken_vaka=geciken_vaka,
        gecikme_orani=gecikme_orani,
        ort_teslim=ort_teslim,
        charts=charts,
        kritik_rows=kritik_rows,
        kritik_hekim_col=C_HEKIM,
        hekim_list=hekim_list,
        selected_hekim=selected_hekim,
        only_delayed=only_delayed,
        detay_table=detay_table,
        insights=insights,
        kritik_limit=kritik_limit,
        kritik_hekim_sayisi=kritik_hekim_sayisi,
    )

