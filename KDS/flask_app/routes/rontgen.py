from flask import Blueprint, render_template
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required  # noqa: E402
from database.xray_loaders import load_xray_analysis_data  # noqa: E402
from routes.dashboard import get_date_range  # noqa: E402

rontgen_bp = Blueprint("rontgen", __name__)


def _find_column(candidates, df_cols):
    for cand in candidates:
        clean = cand.upper().strip()
        for col in df_cols:
            cu = str(col).upper()
            if clean == cu.replace("_", " ").strip() or clean == cu.strip():
                return col
    return None


@rontgen_bp.route("/rontgen")
@login_required
def rontgen():
    sd, ed = get_date_range()
    df_raw = load_xray_analysis_data(sd, ed)

    if df_raw is None or df_raw.empty:
        return render_template("rontgen.html", start_date=sd, end_date=ed, no_data=True)

    df = df_raw.copy()

    C_HEKIM = _find_column(["DKTAD", "HEKIM ADI", "DOKTOR", "HEKIM"], df.columns)
    C_KLINIK = _find_column(["GSS_KLINIK_ADI", "BRANS_ADI"], df.columns)
    C_PERI = _find_column(["PERIAPICAL RÖNTGEN SAYISI", "PERIAPIKAL RÖNTGEN SAYISI"], df.columns)
    C_PAN = _find_column(["PANORAMIK RÖNTGEN SAYISI"], df.columns)
    C_SEF = _find_column(["SEFALOMETRIK RÖNTGEN SAYISI"], df.columns)
    C_TOMO = _find_column(["DENTAL TOMOGRAFI RÖNTGEN SAYISI"], df.columns)

    if not C_HEKIM or not C_PAN:
        return render_template("rontgen.html", start_date=sd, end_date=ed, no_data=True)

    film_cols = [c for c in [C_PERI, C_PAN, C_SEF, C_TOMO] if c is not None]
    for col in film_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Genel metrikler
    df["TOPLAM_FILM"] = df[film_cols].sum(axis=1)
    toplam_tetkik = int(df["TOPLAM_FILM"].sum())
    toplam_pan = int(df[C_PAN].sum()) if C_PAN else 0
    toplam_peri = int(df[C_PERI].sum()) if C_PERI else 0

    # ---- Sekme 1: Hekim Analizi ----
    hekim_sum = (
        df.groupby(C_HEKIM)[film_cols]
        .sum()
        .reset_index()
    )
    hekim_sum["TOPLAM_FILM"] = hekim_sum[film_cols].sum(axis=1)
    hekim_sum = hekim_sum.sort_values("TOPLAM_FILM", ascending=False)

    top_n = 15
    hekim_top = hekim_sum.head(top_n)
    hekim_melt = hekim_top.melt(
        id_vars=C_HEKIM, value_vars=film_cols, var_name="Tür", value_name="Adet"
    )
    fig_hekim_bar = px.bar(
        hekim_melt,
        x=C_HEKIM,
        y="Adet",
        color="Tür",
        barmode="group",
        labels={C_HEKIM: "Hekim", "Adet": "Film Sayısı"},
    )
    fig_hekim_bar.update_traces(texttemplate="%{y:.3s}", textposition="outside", cliponaxis=False)
    fig_hekim_bar.update_layout(
        template="plotly_dark",
        height=420,
        margin=dict(l=10, r=10, t=10, b=60),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(tickangle=-45),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    hekim_table = hekim_sum.head(30).to_dict(orient="records")

    # Bilgi şeritleri
    hekim_en_fazla = hekim_sum.iloc[0] if not hekim_sum.empty else None
    hekim_en_az = (
        hekim_sum[hekim_sum["TOPLAM_FILM"] > 0].iloc[-1]
        if (hekim_sum["TOPLAM_FILM"] > 0).any()
        else None
    )

    # ---- Sekme 2: Branş Analizi ----
    branch_pie_html = ""
    branch_type_pie_html = ""
    fig_branch_bar_html = ""
    if C_KLINIK:
        branch_sum = (
            df.groupby(C_KLINIK)[film_cols]
            .sum()
            .reset_index()
        )
        branch_sum["TOPLAM_FILM"] = branch_sum[film_cols].sum(axis=1)
        branch_sum = branch_sum.sort_values("TOPLAM_FILM", ascending=False)

        fig_branch_pie = px.pie(
            branch_sum,
            names=C_KLINIK,
            values="TOPLAM_FILM",
            hole=0.55,
        )
        fig_branch_pie.update_layout(
            template="plotly_dark",
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        total_by_type = df[film_cols].sum().reset_index()
        total_by_type.columns = ["TUR", "ADET"]
        fig_type_pie = px.pie(
            total_by_type,
            names="TUR",
            values="ADET",
            hole=0.55,
        )
        fig_type_pie.update_layout(
            template="plotly_dark",
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        fig_branch_bar = px.bar(
            branch_sum.head(10).sort_values("TOPLAM_FILM"),
            x="TOPLAM_FILM",
            y=C_KLINIK,
            orientation="h",
            labels={"TOPLAM_FILM": "Toplam Film Sayısı", C_KLINIK: ""},
        )
        fig_branch_bar.update_traces(texttemplate="%{x:.3s}", textposition="outside", cliponaxis=False)
        fig_branch_bar.update_layout(
            template="plotly_dark",
            height=360,
            margin=dict(l=10, r=50, t=10, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )

        cfg = {"responsive": True}
        branch_pie_html = fig_branch_pie.to_html(full_html=False, include_plotlyjs=False, config=cfg)
        branch_type_pie_html = fig_type_pie.to_html(full_html=False, include_plotlyjs=False, config=cfg)
        fig_branch_bar_html = fig_branch_bar.to_html(full_html=False, include_plotlyjs=False, config=cfg)

    # ---- Sekme 3: Yoğunluk (Hekim x Tetkik Türü heatmap) ----
    heat_html = ""
    if not hekim_top.empty:
        heat_df = hekim_top.set_index(C_HEKIM)[film_cols]
        fig_heat = go.Figure(
            data=go.Heatmap(
                z=heat_df.values,
                x=list(heat_df.columns),
                y=list(heat_df.index),
                colorscale="YlOrRd",
                colorbar=dict(title="Film Sayısı"),
                text=heat_df.values,
                texttemplate="%{text}",
                hovertemplate="<b>%{y}</b><br>%{x}: %{z}<extra></extra>",
            )
        )
        fig_heat.update_layout(
            template="plotly_dark",
            height=420,
            margin=dict(l=80, r=40, t=10, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title="Tetkik Türü"),
            yaxis=dict(title="Hekim"),
        )
        cfg = {"responsive": True}
        heat_html = fig_heat.to_html(full_html=False, include_plotlyjs=False, config=cfg)

    # ---- Sekme 4: Verimlilik & Anomali (Panoramik / Periapikal tercih oranı) ----
    verim_html = ""
    box_html = ""
    if C_PAN and C_PERI:
        ratio_df = hekim_sum.copy()
        # Panoramik / Periapikal oranı (Periapikal 0 ise oran 0 kabul)
        denom = ratio_df[C_PERI].replace(0, pd.NA)
        ratio_df["TERCIH_ORAN"] = (ratio_df[C_PAN] / denom).fillna(0.0)

        fig_scatter = px.scatter(
            ratio_df,
            x="TOPLAM_FILM",
            y="TERCIH_ORAN",
            size="TOPLAM_FILM",
            color="TERCIH_ORAN",
            color_continuous_scale="Viridis",
            hover_name=C_HEKIM,
            labels={
                "TOPLAM_FILM": "Toplam Film",
                "TERCIH_ORAN": "Panoramik / Periapikal Oran",
            },
        )
        fig_scatter.update_traces(marker=dict(opacity=0.85))
        fig_scatter.update_layout(
            template="plotly_dark",
            height=380,
            margin=dict(l=10, r=20, t=10, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            coloraxis_colorbar=dict(title="Oran"),
        )

        if C_KLINIK:
            ratio_df_branch = ratio_df.copy()
            # Hekim-satırları ile klinik bilgisini join et
            klinik_map = df.set_index(C_HEKIM)[C_KLINIK].to_dict()
            ratio_df_branch[C_KLINIK] = ratio_df_branch[C_HEKIM].map(klinik_map)

            fig_box = px.box(
                ratio_df_branch.dropna(subset=[C_KLINIK]),
                x=C_KLINIK,
                y="TERCIH_ORAN",
                points="outliers",
                labels={
                    C_KLINIK: "Branş",
                    "TERCIH_ORAN": "Panoramik / Periapikal Oran",
                },
            )
            fig_box.update_layout(
                template="plotly_dark",
                height=380,
                margin=dict(l=10, r=20, t=10, b=80),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(tickangle=-45),
            )
        else:
            fig_box = go.Figure()

        cfg = {"responsive": True}
        verim_html = fig_scatter.to_html(
            full_html=False, include_plotlyjs=False, config=cfg
        )
        box_html = fig_box.to_html(
            full_html=False, include_plotlyjs=False, config=cfg
        )

    cfg_main = {"responsive": True}
    charts = {
        "fig_hekim_bar": fig_hekim_bar.to_html(
            full_html=False, include_plotlyjs=False, config=cfg_main
        ),
        "fig_heat": heat_html,
        "branch_pie": branch_pie_html,
        "type_pie": branch_type_pie_html,
        "branch_bar": fig_branch_bar_html,
        "verim_scatter": verim_html,
        "verim_box": box_html,
    }

    return render_template(
        "rontgen.html",
        start_date=sd,
        end_date=ed,
        no_data=False,
        toplam_tetkik=toplam_tetkik,
        toplam_pan=toplam_pan,
        toplam_peri=toplam_peri,
        charts=charts,
        hekim_table=hekim_table,
        hekim_en_fazla=hekim_en_fazla,
        hekim_en_az=hekim_en_az,
    )

