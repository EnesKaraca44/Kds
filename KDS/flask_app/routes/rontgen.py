from flask import Blueprint, render_template
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required  # noqa: E402
from database.rontgen_sorgular import rontgen_verisi_yukle  # noqa: E402
from routes.dashboard import get_date_range  # noqa: E402

rontgen_bp = Blueprint("rontgen", __name__)


def _find_column(candidates, df_cols):
    for cand in candidates:
        clean = _normalize_col_name(cand)
        for col in df_cols:
            cu = _normalize_col_name(col)
            if clean == cu:
                return col
    return None


def _normalize_col_name(value):
    text = str(value).upper().replace("_", " ").strip()
    text = text.replace("�", "")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _short_type_name(col_name):
    normalized = _normalize_col_name(col_name)
    if "PERIAPIKAL" in normalized or "PERIAPICAL" in normalized:
        return "Periapikal"
    if "PANORAMIK" in normalized or "PANORAMIC" in normalized:
        return "Panoramik"
    if "SEFALOMETRIK" in normalized:
        return "Sefalometrik"
    if "TOMOGRAFI" in normalized:
        return "Tomografi"
    return str(col_name)


def _empty_chart_html(message, height=320):
    fig = go.Figure()
    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        annotations=[
            dict(
                text=message,
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=15),
            )
        ],
    )
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


@rontgen_bp.route("/rontgen")
@login_required
def rontgen():
    sd, ed = get_date_range()
    df_raw = rontgen_verisi_yukle(sd, ed)

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
    heat_html = _empty_chart_html("Secilen aralikta yogunluk verisi bulunamadi.", height=420)
    heatmap_columns = []
    heatmap_rows = []
    if not hekim_top.empty:
        heat_df = hekim_top.set_index(C_HEKIM)[film_cols].copy()
        heat_df = heat_df.loc[heat_df.sum(axis=1) > 0]
        heat_df = heat_df.loc[:, heat_df.sum(axis=0) > 0]

        if not heat_df.empty:
            heat_df.columns = [_short_type_name(col) for col in heat_df.columns]
            heatmap_columns = list(heat_df.columns)
            col_max = {
                col: max(_safe_float(heat_df[col].max()), 1.0)
                for col in heat_df.columns
            }
            for doctor_name, row in heat_df.iterrows():
                cells = []
                for col in heat_df.columns:
                    value = int(_safe_float(row[col]))
                    intensity = int(round((value / col_max[col]) * 100)) if col_max[col] else 0
                    cells.append({
                        "label": col,
                        "value": value,
                        "intensity": intensity,
                    })
                heatmap_rows.append({
                    "hekim": doctor_name,
                    "cells": cells,
                    "toplam": int(sum(cell["value"] for cell in cells)),
                })

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
    verim_html = _empty_chart_html("Panoramik / Periapikal denge verisi bulunamadi.", height=380)
    verim_scatter_points = []
    verim_scatter_x_max = 100.0
    verim_scatter_y_max = 2.0
    ratio_rows = []
    box_html = _empty_chart_html("Anomali kutu grafigi icin brans verisi bulunamadi.", height=380)
    if C_PAN and C_PERI:
        ratio_df = hekim_sum.copy()
        ratio_df = ratio_df[ratio_df["TOPLAM_FILM"] > 0].copy()
        ratio_df = ratio_df[(ratio_df[C_PAN] > 0) | (ratio_df[C_PERI] > 0)].copy()
        # Panoramik / Periapikal oranı (Periapikal 0 ise oran 0 kabul)
        denom = ratio_df[C_PERI].replace(0, pd.NA)
        ratio_df["TERCIH_ORAN"] = (ratio_df[C_PAN] / denom).fillna(0.0)
        if not ratio_df.empty:
            ratio_x_max = float(ratio_df["TOPLAM_FILM"].quantile(0.98))
            ratio_y_max = float(ratio_df["TERCIH_ORAN"].quantile(0.95))
            ratio_x_max = max(ratio_x_max * 1.1, float(ratio_df["TOPLAM_FILM"].max()) * 0.35, 100.0)
            ratio_y_max = max(ratio_y_max * 1.15, 2.0)
            verim_scatter_x_max = ratio_x_max
            verim_scatter_y_max = ratio_y_max
            verim_scatter_points = (
                ratio_df[[C_HEKIM, "TOPLAM_FILM", "TERCIH_ORAN", C_PAN, C_PERI]]
                .rename(
                    columns={
                        C_HEKIM: "hekim",
                        "TOPLAM_FILM": "toplam_film",
                        "TERCIH_ORAN": "tercih_oran",
                        C_PAN: "panoramik",
                        C_PERI: "periapikal",
                    }
                )
                .to_dict(orient="records")
            )
            for row in (
                ratio_df[[C_HEKIM, "TOPLAM_FILM", "TERCIH_ORAN", C_PAN, C_PERI]]
                .sort_values("TOPLAM_FILM", ascending=False)
                .head(30)
                .to_dict(orient="records")
            ):
                oran = _safe_float(row["TERCIH_ORAN"])
                if oran >= 1.2:
                    yorum = "Panoramik agirlikli"
                elif oran <= 0.8:
                    yorum = "Periapikal agirlikli"
                else:
                    yorum = "Dengeli"
                ratio_rows.append({
                    "hekim": row[C_HEKIM],
                    "toplam_film": int(_safe_float(row["TOPLAM_FILM"])),
                    "panoramik": int(_safe_float(row[C_PAN])),
                    "periapikal": int(_safe_float(row[C_PERI])),
                    "oran": round(oran, 2),
                    "bar_width": max(6, min(int((oran / max(ratio_y_max, 0.1)) * 100), 100)),
                    "yorum": yorum,
                })

            fig_scatter = go.Figure(
                data=[
                    go.Scatter(
                        x=ratio_df["TOPLAM_FILM"],
                        y=ratio_df["TERCIH_ORAN"],
                        mode="markers",
                        text=ratio_df[C_HEKIM],
                        customdata=ratio_df[[C_PAN, C_PERI]].to_numpy(),
                        hovertemplate=(
                            "<b>%{text}</b><br>"
                            "Toplam Film: %{x}<br>"
                            "Panoramik / Periapikal Oran: %{y:.2f}<br>"
                            "Panoramik: %{customdata[0]}<br>"
                            "Periapikal: %{customdata[1]}<extra></extra>"
                        ),
                        marker=dict(
                            size=14,
                            color="#2563eb",
                            opacity=0.82,
                            line=dict(color="#ffffff", width=1.2),
                        ),
                    )
                ]
            )
            fig_scatter.update_layout(
                template="plotly_dark",
                height=380,
                margin=dict(l=10, r=20, t=10, b=40),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                coloraxis_colorbar=dict(title="Oran"),
                xaxis=dict(title="Toplam Film", range=[0, ratio_x_max]),
                yaxis=dict(title="Panoramik / Periapikal Oran", range=[0, ratio_y_max]),
                uirevision="rontgen-verim-scatter",
            )

            if C_KLINIK:
                ratio_df_branch = ratio_df.copy()
                klinik_map = (
                    df[[C_HEKIM, C_KLINIK]]
                    .dropna(subset=[C_HEKIM, C_KLINIK])
                    .drop_duplicates(subset=[C_HEKIM])
                    .set_index(C_HEKIM)[C_KLINIK]
                    .to_dict()
                )
                ratio_df_branch[C_KLINIK] = ratio_df_branch[C_HEKIM].map(klinik_map)
                ratio_df_branch = ratio_df_branch.dropna(subset=[C_KLINIK])

                if not ratio_df_branch.empty:
                    fig_box = px.box(
                        ratio_df_branch,
                        x=C_KLINIK,
                        y="TERCIH_ORAN",
                        points="all",
                        labels={
                            C_KLINIK: "Branş",
                            "TERCIH_ORAN": "Panoramik / Periapikal Oran",
                        },
                    )
                    fig_box.update_traces(
                        jitter=0.35,
                        pointpos=0,
                        marker=dict(size=7, opacity=0.7, color="#2563eb"),
                        line=dict(color="#1d4ed8", width=2),
                        fillcolor="rgba(37, 99, 235, 0.18)",
                    )
                    fig_box.update_layout(
                        template="plotly_dark",
                        height=380,
                        margin=dict(l=10, r=20, t=10, b=80),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        xaxis=dict(tickangle=-45),
                        yaxis=dict(range=[0, ratio_y_max]),
                        uirevision="rontgen-verim-box",
                    )
                    box_html = fig_box.to_html(
                        full_html=False, include_plotlyjs=False, config={"responsive": True}
                    )

            cfg = {"responsive": True}
            verim_html = fig_scatter.to_html(
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
        verim_scatter_points=verim_scatter_points,
        verim_scatter_x_max=verim_scatter_x_max,
        verim_scatter_y_max=verim_scatter_y_max,
        heatmap_columns=heatmap_columns,
        heatmap_rows=heatmap_rows,
        ratio_rows=ratio_rows,
        hekim_table=hekim_table,
        hekim_en_fazla=hekim_en_fazla,
        hekim_en_az=hekim_en_az,
    )

