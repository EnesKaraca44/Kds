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
from database.rontgen_sorgular import rontgen_verisi_hekim_brans  # noqa: E402
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
    df_hekim, df_brans = rontgen_verisi_hekim_brans(sd, ed)

    if (df_hekim is None or df_hekim.empty) and (df_brans is None or df_brans.empty):
        return render_template("rontgen.html", start_date=sd, end_date=ed, no_data=True)

    film_cols = ["Periapikal", "Panoramik", "Sefalometrik", "DentalTomografi"]
    
    if not df_hekim.empty:
        for col in film_cols:
            if col in df_hekim.columns:
                df_hekim[col] = pd.to_numeric(df_hekim[col], errors="coerce").fillna(0).astype(int)
        df_hekim["TOPLAM_FILM"] = df_hekim[film_cols].sum(axis=1)

    if not df_brans.empty:
        for col in film_cols:
            if col in df_brans.columns:
                df_brans[col] = pd.to_numeric(df_brans[col], errors="coerce").fillna(0).astype(int)
        df_brans["TOPLAM_FILM"] = df_brans[film_cols].sum(axis=1)

    toplam_tetkik = int(df_hekim["TOPLAM_FILM"].sum()) if not df_hekim.empty else 0
    toplam_pan = int(df_hekim["Panoramik"].sum()) if not df_hekim.empty and "Panoramik" in df_hekim.columns else 0
    toplam_peri = int(df_hekim["Periapikal"].sum()) if not df_hekim.empty and "Periapikal" in df_hekim.columns else 0

    C_HEKIM = "DktAd"
    C_KLINIK = "BirimAd"
    C_PAN = "Panoramik"
    C_PERI = "Periapikal"

    # ---- Sekme 1: Hekim Analizi ----
    hekim_sum = df_hekim.sort_values("TOPLAM_FILM", ascending=False).copy() if not df_hekim.empty else pd.DataFrame()
    top_n = 15
    hekim_top = hekim_sum.head(top_n) if not hekim_sum.empty else pd.DataFrame()
    
    # DEBUG LOG
    try:
        with open(r"c:\Users\ENES\Desktop\KDS_enson\KDS\flask_app\df_debug.txt", "w", encoding="utf-8") as f:
            if not hekim_top.empty:
                f.write("hekim_top:\n")
                f.write(hekim_top.to_string())
                hekim_melt = hekim_top.melt(id_vars=C_HEKIM, value_vars=film_cols, var_name="Tür", value_name="Adet")
                f.write("\n\nhekim_melt:\n")
                f.write(hekim_melt.to_string())
            else:
                f.write("hekim_top is empty!\n")
    except Exception:
        pass
        
    fig_hekim_bar_html = _empty_chart_html("NO_DATA_HEKIM", height=420)
    if not hekim_top.empty:
        hekim_melt = hekim_top.melt(id_vars=C_HEKIM, value_vars=film_cols, var_name="Tür", value_name="Adet")
        hekim_melt["Adet"] = pd.to_numeric(hekim_melt["Adet"], errors='coerce').fillna(0).astype(int)
        
        fig_hekim_bar = go.Figure()
        for tur in film_cols:
            df_tur = hekim_melt[hekim_melt["Tür"] == tur]
            fig_hekim_bar.add_trace(go.Bar(
                x=df_tur[C_HEKIM].tolist(),
                y=df_tur["Adet"].tolist(),
                name=tur,
                text=df_tur["Adet"].tolist(),
                textposition="outside"
            ))
            
        fig_hekim_bar.update_layout(
            barmode="group",
            template="plotly_dark", height=420, margin=dict(l=10, r=10, t=30, b=100),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickangle=-45, title="", automargin=True),
            yaxis=dict(title="", automargin=True),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            autosize=True,
        )
        fig_hekim_bar_html = fig_hekim_bar.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})

    hekim_table = hekim_sum.head(30).to_dict(orient="records") if not hekim_sum.empty else []
    hekim_en_fazla = hekim_sum.iloc[0] if not hekim_sum.empty else None
    hekim_en_az = (hekim_sum[hekim_sum["TOPLAM_FILM"] > 0].iloc[-1] if not hekim_sum.empty and (hekim_sum["TOPLAM_FILM"] > 0).any() else None)

    # ---- Sekme 2: Branş Analizi ----
    branch_pie_html = ""
    branch_type_pie_html = ""
    fig_branch_bar_html = ""
    
    if not df_brans.empty:
        branch_sum = df_brans.sort_values("TOPLAM_FILM", ascending=False).copy()
        fig_branch_pie = px.pie(branch_sum, names=C_KLINIK, values="TOPLAM_FILM", hole=0.55)
        fig_branch_pie.update_layout(template="plotly_dark", margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

        total_by_type = branch_sum[film_cols].sum().reset_index()
        total_by_type.columns = ["TUR", "ADET"]
        fig_type_pie = px.pie(total_by_type, names="TUR", values="ADET", hole=0.55)
        fig_type_pie.update_layout(template="plotly_dark", margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

        fig_branch_bar = px.bar(
            branch_sum.head(10).sort_values("TOPLAM_FILM"), x="TOPLAM_FILM", y=C_KLINIK, orientation="h",
            labels={"TOPLAM_FILM": "", C_KLINIK: ""},
        )
        fig_branch_bar.update_traces(texttemplate="%{x}", textposition="outside", cliponaxis=False)
        fig_branch_bar.update_xaxes(type="linear")
        fig_branch_bar.update_layout(
            template="plotly_dark", height=360, margin=dict(l=10, r=50, t=10, b=40),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False,
        )

        cfg = {"responsive": True}
        branch_pie_html = fig_branch_pie.to_html(full_html=False, include_plotlyjs=False, config=cfg)
        branch_type_pie_html = fig_type_pie.to_html(full_html=False, include_plotlyjs=False, config=cfg)
        fig_branch_bar_html = fig_branch_bar.to_html(full_html=False, include_plotlyjs=False, config=cfg)

    # ---- Sekme 3: Yoğunluk ----
    heat_html = _empty_chart_html("NO_DATA_HEAT", height=420)
    heatmap_columns = []
    heatmap_rows = []
    if not hekim_top.empty:
        heat_df = hekim_top.set_index(C_HEKIM)[film_cols].copy()
        heat_df = heat_df.loc[heat_df.sum(axis=1) > 0]
        heat_df = heat_df.loc[:, heat_df.sum(axis=0) > 0]

        if not heat_df.empty:
            heatmap_columns = list(heat_df.columns)
            col_max = {col: max(_safe_float(heat_df[col].max()), 1.0) for col in heat_df.columns}
            for doctor_name, row in heat_df.iterrows():
                cells = []
                for col in heat_df.columns:
                    value = int(_safe_float(row[col]))
                    intensity = int(round((value / col_max[col]) * 100)) if col_max[col] else 0
                    cells.append({"label": col, "value": value, "intensity": intensity})
                heatmap_rows.append({"hekim": doctor_name, "cells": cells, "toplam": int(sum(c["value"] for c in cells))})

            fig_heat = go.Figure(
                data=go.Heatmap(
                    z=heat_df.values, x=list(heat_df.columns), y=list(heat_df.index),
                    colorscale="YlOrRd", colorbar=dict(title="Film Sayısı"),
                    text=heat_df.values, texttemplate="%{text}", hovertemplate="<b>%{y}</b><br>%{x}: %{z}<extra></extra>",
                )
            )
            fig_heat.update_layout(
                template="plotly_dark", height=420, margin=dict(l=80, r=40, t=10, b=40),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(title=""), yaxis=dict(title=""),
            )
            heat_html = fig_heat.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})

    # ---- Sekme 4: Verimlilik & Anomali ----
    verim_html = _empty_chart_html("Panoramik / Periapikal denge verisi bulunamadi.", height=380)
    verim_scatter_points = []
    verim_scatter_x_max = 100.0
    verim_scatter_y_max = 2.0
    ratio_rows = []
    box_html = _empty_chart_html("İleri tetkik (Sefalometrik & Tomografi) verisi bulunamadı.", height=380)
    
    if not hekim_sum.empty and ("Sefalometrik" in hekim_sum.columns or "DentalTomografi" in hekim_sum.columns):
        ileri_cols = [c for c in ["Sefalometrik", "DentalTomografi"] if c in hekim_sum.columns]
        if ileri_cols:
            ileri_df = hekim_sum[hekim_sum[ileri_cols].sum(axis=1) > 0].copy()
            ileri_df["ILERI_TOPLAM"] = ileri_df[ileri_cols].sum(axis=1)
            ileri_df = ileri_df.sort_values("ILERI_TOPLAM", ascending=False).head(15)
            
            if not ileri_df.empty:
                ileri_melt = ileri_df.melt(id_vars=C_HEKIM, value_vars=ileri_cols, var_name="Tür", value_name="Adet")
                ileri_melt["Adet"] = pd.to_numeric(ileri_melt["Adet"], errors='coerce').fillna(0).astype(int)
                
                fig_ileri = go.Figure()
                colors = ["#f59e0b", "#ec4899"]
                for i, tur in enumerate(ileri_cols):
                    df_tur = ileri_melt[ileri_melt["Tür"] == tur]
                    fig_ileri.add_trace(go.Bar(
                        x=df_tur[C_HEKIM].tolist(),
                        y=df_tur["Adet"].tolist(),
                        name=tur,
                        text=df_tur["Adet"].tolist(),
                        textposition="outside",
                        marker_color=colors[i % len(colors)]
                    ))

                fig_ileri.update_layout(
                    barmode="group",
                    template="plotly_dark", height=380, margin=dict(l=10, r=10, t=10, b=60),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(tickangle=-45, title=""),
                    yaxis=dict(title=""),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                box_html = fig_ileri.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})
    
    if not hekim_sum.empty:
        ratio_df = hekim_sum.copy()
        ratio_df = ratio_df[ratio_df["TOPLAM_FILM"] > 0].copy()
        ratio_df = ratio_df[(ratio_df[C_PAN] > 0) | (ratio_df[C_PERI] > 0)].copy()
        
        def _calc_ratio(row):
            pan = _safe_float(row[C_PAN])
            peri = _safe_float(row[C_PERI])
            if peri == 0:
                return 99.0 if pan > 0 else 1.0
            return pan / peri
        
        ratio_df["TERCIH_ORAN"] = ratio_df.apply(_calc_ratio, axis=1)
        
        if not ratio_df.empty:
            ratio_x_max = float(ratio_df["TOPLAM_FILM"].quantile(0.98))
            ratio_y_max = float(ratio_df["TERCIH_ORAN"].quantile(0.95))
            ratio_x_max = max(ratio_x_max * 1.1, float(ratio_df["TOPLAM_FILM"].max()) * 0.35, 100.0)
            ratio_y_max = max(ratio_y_max * 1.15, 2.0)
            verim_scatter_x_max = ratio_x_max
            verim_scatter_y_max = ratio_y_max
            
            for row in (ratio_df[[C_HEKIM, "TOPLAM_FILM", "TERCIH_ORAN", C_PAN, C_PERI]]
                        .sort_values("TOPLAM_FILM", ascending=False).head(30)
                        .to_dict(orient="records")):
                oran = _safe_float(row["TERCIH_ORAN"])
                if oran >= 1.2:
                    yorum = "Panoramik agirlikli"
                elif oran <= 0.8:
                    yorum = "Periapikal agirlikli"
                else:
                    yorum = "Dengeli"
                    
                ratio_rows.append({
                    "hekim": row[C_HEKIM], "toplam_film": int(_safe_float(row["TOPLAM_FILM"])),
                    "panoramik": int(_safe_float(row[C_PAN])), "periapikal": int(_safe_float(row[C_PERI])),
                    "oran": round(oran, 2), "bar_width": max(6, min(int((oran / max(ratio_y_max, 0.1)) * 100), 100)),
                    "yorum": yorum,
                })

            fig_scatter = go.Figure(
                data=[
                    go.Scatter(
                        x=ratio_df["TOPLAM_FILM"], y=ratio_df["TERCIH_ORAN"],
                        mode="markers", text=ratio_df[C_HEKIM],
                        customdata=ratio_df[[C_PAN, C_PERI]].to_numpy(),
                        hovertemplate=("<b>%{text}</b><br>Toplam Film: %{x}<br>Panoramik / Periapikal Oran: %{y:.2f}<br>"
                                       "Panoramik: %{customdata[0]}<br>Periapikal: %{customdata[1]}<extra></extra>"),
                        marker=dict(size=14, color="#2563eb", opacity=0.82, line=dict(color="#ffffff", width=1.2)),
                    )
                ]
            )
            fig_scatter.update_layout(
                template="plotly_dark", height=380, margin=dict(l=10, r=20, t=10, b=40),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                coloraxis_colorbar=dict(title=""), xaxis=dict(title="", range=[0, ratio_x_max]),
                yaxis=dict(title="", range=[0, ratio_y_max]), uirevision="rontgen-verim-scatter",
            )
            verim_html = fig_scatter.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})

    charts = {
        "fig_hekim_bar": fig_hekim_bar_html,
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

