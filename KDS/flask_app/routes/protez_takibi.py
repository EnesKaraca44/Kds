from flask import Blueprint, render_template, request
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required  # noqa: E402
from routes.dashboard import get_date_range  # noqa: E402
from database.protez_takibi_sorgular import (  # noqa: E402
    asama_girilmemis_hasta_listesi_yukle,
    protez_suresi_gecen_hasta_birim_yukle,
)


protez_takibi_bp = Blueprint("protez_takibi", __name__)

PAGE_SQL_KODLARI = [
    "protez_takibi.asama_girilmemis_hasta_listesi_yukle",
    "protez_takibi.protez_suresi_gecen_hasta_birim_yukle",
]

# SQL kolon adlari -> tabloda gorunen Turkce basliklar
PT_KOLON_ETIKETLERI = {
    "dosyaNo": "Dosya No",
    "hastaAdSoyad": "Hasta",
    "doktorAdSoyad": "Hekim",
    "hizmetSutTanimi": "İşlem",
    "hizmetSutKodu": "SUT Kodu",
    "tarihFark": "Geçen Süre (Gün)",
    "servisAd": "Servis",
    "islemTarihi": "İşlem Tarihi",
}

ASAMA_LISTE_KOLONLARI = [
    "dosyaNo",
    "hastaAdSoyad",
    "doktorAdSoyad",
    "servisAd",
    "hizmetSutKodu",
    "hizmetSutTanimi",
    "islemTarihi",
    "tarihFark",
]


@protez_takibi_bp.route("/protez-takibi")
@login_required
def protez_takibi():
    sd, ed = get_date_range()
    hizmet_sut_kodu = (request.args.get("hizmet_sut_kodu") or "").strip() or None
    islem_tarihi = (request.args.get("islem_tarihi") or "").strip() or None
    birim_id_raw = (request.args.get("birim_id") or "").strip()
    birim_id = int(birim_id_raw) if birim_id_raw.isdigit() else None

    df_asama = asama_girilmemis_hasta_listesi_yukle(
        hizmet_sut_kodu=hizmet_sut_kodu,
        islem_tarihi=islem_tarihi,
        birim_id=birim_id,
    )
    df_rpt = protez_suresi_gecen_hasta_birim_yukle(
        birim_id_csv=birim_id_raw if birim_id_raw else None
    )

    if df_asama is None:
        df_asama = pd.DataFrame()
    if df_rpt is None:
        df_rpt = pd.DataFrame()

    print(
        "[PROTEZ_TAKIBI] "
        f"params(hizmet_sut_kodu={hizmet_sut_kodu}, islem_tarihi={islem_tarihi}, birim_id={birim_id_raw or None}) "
        f"rows(asama={len(df_asama)}, rpt={len(df_rpt)})"
    )

    toplam_hasta = 0
    if "hastaKimlikId" in df_rpt.columns:
        toplam_hasta = int(df_rpt["hastaKimlikId"].nunique())
    elif "hastaKimlikId" in df_asama.columns:
        toplam_hasta = int(df_asama["hastaKimlikId"].nunique())

    toplam_islem = int(len(df_rpt))

    # Kartlar: T2/T3 ve RPT, df_rpt icindeki sure (0-3 trafik) ile hizalanir; grafiklerle ayni mantik.
    sure_ser = None
    if not df_rpt.empty and "sure" in df_rpt.columns:
        sure_ser = (
            pd.to_numeric(df_rpt["sure"], errors="coerce")
            .fillna(0)
            .round(0)
            .astype(int)
            .clip(0, 3)
        )

    if sure_ser is not None:
        devam_eden = int((sure_ser == 2).sum())
        tamamlanan = int((sure_ser == 3).sum())
        rpt_adedi = tamamlanan
        genel_rpt_orani = float((sure_ser == 3).mean() * 100.0) if toplam_islem > 0 else 0.0
    else:
        devam_eden = int(len(df_asama))
        tamamlanan = max(toplam_islem - devam_eden, 0)
        rpt_adedi = 0
        genel_rpt_orani = 0.0

    # Sekme 1: En yogun hekim grafigi
    fig_hekim = go.Figure()
    has_hekim_data = False
    if not df_rpt.empty and "doktorAdSoyad" in df_rpt.columns:
        hekim_df = (
            df_rpt.groupby("doktorAdSoyad")
            .size()
            .reset_index(name="adet")
            .sort_values("adet", ascending=False)
            .head(15)
        )
        has_hekim_data = not hekim_df.empty
        fig_hekim = px.bar(
            hekim_df.sort_values("adet"),
            x="adet",
            y="doktorAdSoyad",
            orientation="h",
            labels={"adet": "Adet", "doktorAdSoyad": ""},
            color="adet",
            color_continuous_scale="Blues",
        )
    fig_hekim.update_layout(
        template="plotly_dark",
        height=360,
        margin=dict(l=10, r=10, t=10, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
    )

    # Sekme 1: Servis dagilim (lab hacmi yerine)
    fig_servis = go.Figure()
    has_servis_data = False
    if not df_rpt.empty and "servisAd" in df_rpt.columns:
        servis_df = (
            df_rpt.groupby("servisAd")
            .size()
            .reset_index(name="adet")
            .sort_values("adet", ascending=False)
            .head(10)
        )
        has_servis_data = not servis_df.empty
        fig_servis = px.pie(
            servis_df,
            names="servisAd",
            values="adet",
            hole=0.45,
        )
    fig_servis.update_layout(
        template="plotly_dark",
        height=360,
        margin=dict(l=10, r=10, t=10, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(font=dict(size=10)),
    )

    # Sekme 2: Hekim bazli RPT performans
    fig_rpt = go.Figure()
    if not df_rpt.empty and "doktorAdSoyad" in df_rpt.columns:
        if "sure" in df_rpt.columns:
            perf = (
                df_rpt.groupby("doktorAdSoyad")
                .agg(
                    asil_islem=("dosyaNo", "count"),
                    rpt_adedi=("sure", lambda x: int((x == 3).sum())),
                    rpt_orani=("sure", lambda x: float((x == 3).mean() * 100)),
                )
                .reset_index()
                .sort_values("rpt_orani", ascending=False)
                .head(15)
            )
        else:
            perf = (
                df_rpt.groupby("doktorAdSoyad")
                .agg(asil_islem=("dosyaNo", "count"))
                .reset_index()
                .sort_values("asil_islem", ascending=False)
                .head(15)
            )
            perf["rpt_adedi"] = 0
            perf["rpt_orani"] = 0.0
        fig_rpt.add_trace(
            go.Scatter(
                x=perf["doktorAdSoyad"],
                y=perf["asil_islem"],
                mode="lines+markers",
                name="Asıl İşlem",
                line=dict(color="#10b981", width=3),
            )
        )
        fig_rpt.add_trace(
            go.Scatter(
                x=perf["doktorAdSoyad"],
                y=perf["rpt_adedi"],
                mode="lines+markers",
                name="RPT Adedi",
                line=dict(color="#ef4444", width=2),
            )
        )
        fig_rpt.add_trace(
            go.Scatter(
                x=perf["doktorAdSoyad"],
                y=perf["rpt_orani"],
                mode="lines+markers",
                name="RPT Oranı (%)",
                line=dict(color="#60a5fa", width=2, dash="dot"),
                yaxis="y2",
            )
        )
    fig_rpt.update_layout(
        template="plotly_dark",
        height=420,
        margin=dict(l=10, r=10, t=10, b=70),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(tickangle=-45),
        yaxis=dict(title="Adet"),
        yaxis2=dict(title="Oran (%)", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    # Sekme 3: Kritik takip listeleri
    # tarihFark (SQL): DATEDIFF(gun, islemTarihi, bugun) — islemin baslangicindan bu yana gecen gun
    kritik_30gun_rows = []
    kritik_30gun_columns = []
    if not df_rpt.empty:
        kritik_df = df_rpt.copy()
        if "tarihFark" in kritik_df.columns:
            kritik_df["tarihFark"] = (
                pd.to_numeric(kritik_df["tarihFark"], errors="coerce").fillna(0).round(0).astype(int)
            )
            kritik_df = kritik_df[kritik_df["tarihFark"] >= 30]
        kritik_cols = [
            "dosyaNo",
            "hastaAdSoyad",
            "doktorAdSoyad",
            "hizmetSutTanimi",
            "tarihFark",
        ]
        kritik_30gun_columns = [c for c in kritik_cols if c in kritik_df.columns]
        if kritik_30gun_columns:
            kritik_30gun_rows = kritik_df[kritik_30gun_columns].head(200).to_dict(orient="records")

    asama_girilmemis_rows = []
    asama_girilmemis_columns = []
    if not df_asama.empty:
        asama_df = df_asama.copy()
        if "tarihFark" in asama_df.columns:
            asama_df["tarihFark"] = (
                pd.to_numeric(asama_df["tarihFark"], errors="coerce").fillna(0).round(0).astype(int)
            )
        asama_girilmemis_columns = [c for c in ASAMA_LISTE_KOLONLARI if c in asama_df.columns]
        if not asama_girilmemis_columns:
            asama_girilmemis_columns = list(asama_df.columns)
        hekim_col = next(
            (c for c in ("doktorAdSoyad", "doktorAd", "hekimAdSoyad") if c in asama_df.columns),
            None,
        )
        if hekim_col:
            asama_df = asama_df.sort_values(
                by=hekim_col,
                key=lambda s: s.astype(str).str.casefold(),
                na_position="last",
            )
        asama_girilmemis_rows = asama_df[asama_girilmemis_columns].head(500).to_dict(orient="records")

    # Sekme 4: Islem dagilimi
    fig_top_islem = go.Figure()
    fig_kirilim = go.Figure()
    has_top_islem_data = False
    has_kirilim_data = False
    if not df_rpt.empty and "hizmetSutTanimi" in df_rpt.columns:
        top_islem_df = (
            df_rpt.groupby("hizmetSutTanimi")
            .size()
            .reset_index(name="adet")
            .sort_values("adet", ascending=False)
            .head(10)
        )
        if not top_islem_df.empty:
            has_top_islem_data = True
            fig_top_islem = px.bar(
                top_islem_df.sort_values("adet"),
                x="adet",
                y="hizmetSutTanimi",
                orientation="h",
                labels={"adet": "Adet", "hizmetSutTanimi": ""},
                color="adet",
                color_continuous_scale="Blues",
            )

            kirilim_df = (
                df_rpt.groupby(["hizmetSutTanimi", "servisAd"])
                .size()
                .reset_index(name="adet")
                .sort_values("adet", ascending=False)
            ) if "servisAd" in df_rpt.columns else pd.DataFrame()

            if not kirilim_df.empty:
                has_kirilim_data = True
                fig_kirilim = px.sunburst(
                    kirilim_df,
                    path=["hizmetSutTanimi", "servisAd"],
                    values="adet",
                )

    fig_top_islem.update_layout(
        template="plotly_dark",
        height=380,
        margin=dict(l=10, r=10, t=10, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
    )
    fig_kirilim.update_layout(
        template="plotly_dark",
        height=380,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    # Sekme 5: Islem listesi (sure kolonu gosterilmez; durumEtiketi renkli rozet)
    islem_listesi_rows = []
    islem_listesi_columns = []
    if not df_rpt.empty:
        list_cols = [
            "dosyaNo",
            "hastaAdSoyad",
            "islemTarihi",
            "hizmetSutTanimi",
            "DIS_NO",
            "doktorAdSoyad",
            "servisAd",
        ]
        list_cols = [c for c in list_cols if c in df_rpt.columns]
        if list_cols:
            extra = ["sure"] if "sure" in df_rpt.columns else []
            list_df = df_rpt[list_cols + extra].copy()
            if "sure" in list_df.columns:
                s = pd.to_numeric(list_df["sure"], errors="coerce").fillna(0).round(0).astype(int).clip(0, 3)
                list_df["durumKodu"] = s
                durum_map = {
                    3: "Kritik",
                    2: "Uyarı",
                    1: "Normal",
                    0: "Süre İçinde",
                }
                list_df["durumEtiketi"] = s.map(durum_map).fillna("Bilinmiyor")
                list_df = list_df.drop(columns=["sure"])
            else:
                list_df["durumKodu"] = 0
                list_df["durumEtiketi"] = "—"
            islem_listesi_columns = list_cols + ["durumEtiketi"]
            out_cols = islem_listesi_columns + ["durumKodu"]
            islem_listesi_rows = list_df[out_cols].head(500).to_dict(orient="records")

    cfg = {"responsive": True, "displaylogo": False}
    return render_template(
        "protez_takibi.html",
        start_date=sd,
        end_date=ed,
        toplam_hasta=toplam_hasta,
        toplam_islem=toplam_islem,
        tamamlanan=tamamlanan,
        devam_eden=devam_eden,
        genel_rpt_orani=genel_rpt_orani,
        rpt_adedi=rpt_adedi,
        has_hekim_data=has_hekim_data,
        has_servis_data=has_servis_data,
        has_top_islem_data=has_top_islem_data,
        has_kirilim_data=has_kirilim_data,
        kritik_30gun_rows=kritik_30gun_rows,
        kritik_30gun_columns=kritik_30gun_columns,
        asama_girilmemis_rows=asama_girilmemis_rows,
        asama_girilmemis_columns=asama_girilmemis_columns,
        asama_girilmemis_adet=len(asama_girilmemis_rows),
        pt_kolon_etiketleri=PT_KOLON_ETIKETLERI,
        islem_listesi_rows=islem_listesi_rows,
        islem_listesi_columns=islem_listesi_columns,
        fig_hekim=fig_hekim.to_html(full_html=False, include_plotlyjs=False, config=cfg),
        fig_servis=fig_servis.to_html(full_html=False, include_plotlyjs=False, config=cfg),
        fig_rpt=fig_rpt.to_html(full_html=False, include_plotlyjs=False, config=cfg),
        fig_top_islem=fig_top_islem.to_html(full_html=False, include_plotlyjs=False, config=cfg),
        fig_kirilim=fig_kirilim.to_html(full_html=False, include_plotlyjs=False, config=cfg),
        page_sql_kodlari=PAGE_SQL_KODLARI,
    )
