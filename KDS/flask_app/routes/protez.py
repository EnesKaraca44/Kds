from flask import Blueprint, render_template, request
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required  # noqa: E402
from database.protez_sorgular import protez_verisi_yukle  # noqa: E402
from routes.dashboard import get_date_range  # noqa: E402

protez_bp = Blueprint("protez", __name__)

PAGE_SQL_KODLARI = ["protez.protez_verisi_yukle"]

# Protez takip ile ayni 0-3 trafik isigi (aşama giriş / teslim süresi)
DURUM_ETIKETLERI = {
    0: "Süre içinde",
    1: "Normal",
    2: "Uyarı",
    3: "Kritik",
}


def _normalize_col_name(c):
    """protez_sorgular ile ayni kolon anahtari (Türkçe I/ı, bosluk)."""
    return (
        str(c)
        .strip()
        .replace(" ", "_")
        .replace("ı", "i")
        .replace("İ", "I")
        .upper()
    )


def _find_column(candidates, df_cols):
    for c in candidates:
        key = _normalize_col_name(c)
        if key in df_cols:
            return key
    return None


def _build_detay_columns(df_columns, c_hasta_kod, c_hasta_ad, c_sut):
    if c_hasta_kod and c_hasta_ad:
        detay_cols = [c_hasta_kod, c_hasta_ad]
    else:
        detay_cols = []
    if c_sut:
        detay_cols.append(c_sut)
    detay_cols.append("DURUM")
    detay_cols += ["PLAN", "GERCEK", "GECIKME_GUN"]
    return [c for c in detay_cols if c in df_columns]


def _dedup_vakalar(sub_df, detay_cols):
    """SQL join tekrarlarini birlestir; ozet tablo ile modal ayni sayimi kullanir."""
    if sub_df.empty:
        return sub_df
    if not detay_cols:
        return sub_df
    return sub_df.drop_duplicates(subset=detay_cols, keep="first")


def _build_detay_records(sub_df, detay_cols):
    if not detay_cols or sub_df.empty:
        return []
    d = _dedup_vakalar(sub_df, detay_cols)
    return d[detay_cols].to_dict(orient="records")


def _hekim_ozet_satir(g, detay_cols, kritik_limit):
    d = _dedup_vakalar(g, detay_cols)
    return pd.Series(
        {
            "vaka_sayisi": len(d),
            "geciken_vaka": int(d["GECIKEN"].sum()) if len(d) else 0,
            "ort_gecikme": d["GECIKME_GUN"].mean() if len(d) else 0.0,
            "toplam_gecikme": d["GECIKME_GUN"].sum() if len(d) else 0.0,
            "kritik_vaka": int((d["GECIKME_GUN"] > kritik_limit).sum()) if len(d) else 0,
        }
    )


def _durum_skor_serisi(g: pd.Series, p: pd.Series) -> pd.Series:
    """
    SQL CASE WHEN sirasi ile ayni (ilk kosul kazanir):
      3: gecen gun > hedef
      2: degilse ve gecen > hedef*0.2
      1: degilse ve gecen > hedef*0.3
      0: diger
    gecen = ISTSH_TRH..GETDATE (df['GERCEK']), hedef = PROTEZ_TESLIM_SURE (df['PLAN']).
    """
    g = pd.to_numeric(g, errors="coerce").fillna(0.0)
    p = pd.to_numeric(p, errors="coerce").fillna(0.0)
    m3 = (g > p) & (p > 0)
    m2 = (~m3) & (g > 0.2 * p) & (p > 0)
    m1 = (~m3) & (~m2) & (g > 0.3 * p) & (p > 0)
    d = pd.Series(0, index=g.index, dtype=int)
    d.loc[m3] = 3
    d.loc[m2] = 2
    d.loc[m1] = 1
    return d.clip(0, 3)


@protez_bp.route("/protez")
@login_required
def protez():
    sd, ed = get_date_range()
    df_raw = protez_verisi_yukle(sd, ed)

    if df_raw is None or df_raw.empty:
        return render_template(
            "protez.html",
            start_date=sd,
            end_date=ed,
            no_data=True,
            page_sql_kodlari=PAGE_SQL_KODLARI,
        )

    df = df_raw.copy()
    df.columns = [_normalize_col_name(c) for c in df.columns]

    C_HEKIM = _find_column(
        [
            "HEKIM_ADI",
            "HEKIMAD",
            "DKTAD",
            "DOKTOR_ADI",
            "DOKTORADSOYAD",
            "HEKIM_AD_SOYAD",
            "HEKIM_ADSOYAD",
            "DOKTOR_AD_SOYAD",
            "DOKTOR_ADSOYAD",
            "HEKIM",
            "DOKTOR",
            "DR_ADI",
            "DR_AD_SOYAD",
            "UZMAN_ADI",
        ],
        df.columns,
    )
    # PROTEZ_SURESI_GECMIS_HASTA_LISTESI (SQL ile hizali):
    #   skh.PROTEZ_TESLIM_SURE  -> PROTEZTESLIMSURE : hedef/planlanan teslim suresi (gun)
    #   DATEDIFF(DAY, shh.ISTSH_TRH, GETDATE()) -> TARIHFARK : istem/islem tarihinden bugune gecen gun
    #   CASE ... END AS sure -> SURE : sadece 0-3 trafik isigi (gun degil); hicbir metrikte kullanilmaz
    C_PLAN = _find_column(
        [
            "PLANLANANTESLIMSURESI",
            "PLAN_SURE",
            "HEDEF_GUN",
            "PLANLANAN_SURE",
            "PLANLANAN_GUN",
            "HEDEF_SURE",
            "HEDEF_SURE_GUN",
            "PLAN_GUN",
            "TALEP_GUN",
            "BEKLENEN_GUN",
            "PROTEZTESLIMSURE",
        ],
        df.columns,
    )
    C_GERCEK = _find_column(
        [
            "TARIHFARK",
            "ORTALAMA_TESLIM_SURESI",
            "ORTALAMA_TESLIM_SÜRESI",
            "TESLIM_SURE_GUN",
            "GERCEK_SURE",
            "GERCEKLESEN_SURE",
            "TESLIM_GUN",
            "TESLIM_GUNU",
            "GECEN_GUN",
            "GUN_SAYISI",
            "SURE_GUN",
            "TOPLAM_GUN",
        ],
        df.columns,
    )
    C_SUT = _find_column(
        [
            "SUT_ADI",
            "PROTEZADI",
            "ACIKLAMA",
            "ISLEM_ADI",
            "HIZMETSUTTANIMI",
            "HIZMETSUTKODU",
            "HIZMET_ADI",
            "ISLEM_TANIMI",
            "TETKIK_ADI",
        ],
        df.columns,
    )
    C_HASTA_KOD = _find_column(
        ["HASTA_KODU", "HASTA_KOD", "HASTA_NO", "PROTOCOL", "DOSYANO", "HASTATC"],
        df.columns,
    )
    C_HASTA_AD = _find_column(
        [
            "HASTA_ADI",
            "HASTA_AD",
            "HASTA_AD_SOYAD",
            "HASTAADSOYAD",
            "HASTA_ADSOYAD",
            "HASTA",
        ],
        df.columns,
    )
    C_TEDAVI_TARIH = _find_column(
        [
            "TEDAVI_TARIHI",
            "BITIS_TARIHI",
            "ISLEM_TRH",
            "ISLEM_TARIHI",
            "ISLEMTARIHI",
            "ISTSH_TRH",
            "TESLIM_TRH",
        ],
        df.columns,
    )
    C_AY = _find_column(["AYADI", "AY", "AY_ADI"], df.columns)

    if not C_HEKIM or not C_PLAN or not C_GERCEK:
        print(
            "[PROTEZ] Zorunlu kolonlardan biri yok; gelen kolonlar: "
            f"{list(df.columns)} | hekim={C_HEKIM!r} plan={C_PLAN!r} gercek={C_GERCEK!r}"
        )
        return render_template(
            "protez.html",
            start_date=sd,
            end_date=ed,
            no_data=True,
            page_sql_kodlari=PAGE_SQL_KODLARI,
        )

    if C_PLAN == C_GERCEK:
        print(
            f"[PROTEZ] Uyari: PLAN ve GERCEK ayni kolona bagli ({C_PLAN!r}); "
            "SQL'de ayri hedef ve gercek sure kolonlari olmali."
        )

    print(f"[PROTEZ] Kolon eslesmesi -> PLAN={C_PLAN!r}, GERCEK={C_GERCEK!r}, HEKIM={C_HEKIM!r}")

    # PLAN / GERCEK ayni ondalik hassasiyette (detay tablosu tutarliligi)
    df["PLAN"] = pd.to_numeric(df[C_PLAN], errors="coerce").fillna(0).round(1)
    df["GERCEK"] = pd.to_numeric(df[C_GERCEK], errors="coerce").fillna(0).round(1)
    # Ham fark (gecikmis mi?): GERCEK > PLAN. Gosterimde negatif gecikme olmasin -> 0'a kliple.
    _diff = (df["GERCEK"] - df["PLAN"]).round(1)
    df["GECIKEN"] = _diff > 0
    df["GECIKME_GUN"] = _diff.clip(lower=0)

    if "SURE" in df.columns:
        df["DURUM"] = (
            pd.to_numeric(df["SURE"], errors="coerce").fillna(0).round(0).astype(int).clip(0, 3)
        )
    else:
        df["DURUM"] = _durum_skor_serisi(df["GERCEK"], df["PLAN"])

    pozitif_gecikme = int(df["GECIKEN"].sum())
    if pozitif_gecikme == 0:
        ornek = df[[C_PLAN, C_GERCEK]].head(3).to_dict(orient="records")
        print(
            "[PROTEZ] Uyari: Hicbir satirda gecikme yok (GERCEK > PLAN saglanmiyor). "
            f"Ornek 3 satir: {ornek}"
        )

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

    # ---- Sekme 2: Geciken Hekim Listesi (tum hekimler + modal detay) ----
    detay_cols = _build_detay_columns(df.columns, C_HASTA_KOD, C_HASTA_AD, C_SUT)

    hekim_summary = (
        df.groupby(C_HEKIM)
        .apply(lambda g: _hekim_ozet_satir(g, detay_cols, kritik_limit))
        .reset_index()
        .sort_values("ort_gecikme", ascending=False)
    )
    hekim_summary["ort_gecikme"] = hekim_summary["ort_gecikme"].round(1)
    hekim_summary["toplam_gecikme"] = hekim_summary["toplam_gecikme"].round(1)
    hekim_summary["geciken_vaka"] = hekim_summary["geciken_vaka"].astype(int)
    hekim_rows = hekim_summary.to_dict(orient="records")

    # Liste sirasi hekim_rows ile ayni (index ile eslesme; isim anahtari Turkce karakter/HTML uyumsuzlugu yapmaz)
    hekim_detay_list = []
    for h in hekim_summary[C_HEKIM]:
        sub_all = df[df[C_HEKIM] == h]
        sub_delayed = _dedup_vakalar(sub_all[sub_all["GECIKEN"]], detay_cols)
        hekim_detay_list.append(
            {
                "name": h,
                "all": _build_detay_records(sub_all, detay_cols),
                "delayed": _build_detay_records(sub_delayed, detay_cols),
            }
        )

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
        labels={"GECIKME_GUN": "Gecikme ort. (gün, erken vaka 0)", x_col: "Dönem"},
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
    if not hekim_summary.empty:
        top_kritik = hekim_summary.loc[hekim_summary["kritik_vaka"].idxmax()]
        kritik_adet = int(top_kritik["kritik_vaka"])
        if kritik_adet > 0:
            insights.append(
                f"En riskli hekim: {top_kritik[C_HEKIM]} "
                f"({kritik_limit} günü geçen {kritik_adet} vaka)."
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
        hekim_rows=hekim_rows,
        kritik_hekim_col=C_HEKIM,
        hekim_detay_list=hekim_detay_list,
        detay_columns=detay_cols,
        durum_etiketleri=DURUM_ETIKETLERI,
        insights=insights,
        kritik_limit=kritik_limit,
        kritik_hekim_sayisi=kritik_hekim_sayisi,
        page_sql_kodlari=PAGE_SQL_KODLARI,
    )

