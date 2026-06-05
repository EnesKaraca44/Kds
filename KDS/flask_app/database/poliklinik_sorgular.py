import pandas as pd
from datetime import date, datetime, timedelta
from .baglanti import baglanti_olustur
from .cache_helper import ttl_cache
from .sql_api_client import get_remote_sql


@ttl_cache(maxsize=32, ttl=60)
def poliklinik_performans_verisi_yukle(start_date_str, end_date_str):
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    try:
        sql_query = get_remote_sql(
            "poliklinik.poliklinik_performans_verisi_yukle",
            {"start_date": start_date_str, "end_date": end_date_str},
        )
        if not sql_query:
            return pd.DataFrame()

        if "?" in sql_query:
            start_dt = datetime.strptime(f"{start_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(f"{end_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
            df = pd.read_sql(sql_query, conn, params=[start_dt, end_dt])
        else:
            df = pd.read_sql(sql_query, conn)
        if 'KAYIT_TARIHI' in df.columns:
            df['KAYIT_TARIHI'] = pd.to_datetime(df['KAYIT_TARIHI'])
        if 'HstGelisTrh' in df.columns:
            df['HstGelisTrh'] = pd.to_datetime(df['HstGelisTrh'])
        return df
    except Exception as e:
        print(f"Poliklinik verisi yuklenirken hata: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def _basvuru_date_params(start_date_str, end_date_str):
    return {
        "start_date": start_date_str,
        "end_date": end_date_str,
        "basTrh": start_date_str,
        "bitTrh": end_date_str,
        "BAS_TRH": start_date_str,
        "BIT_TRH": end_date_str,
        "BASLANGIC_TRH": start_date_str,
        "BITIS_TRH": end_date_str,
    }


def _fetch_basvuru_df(rapor_kod, params):
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()
    try:
        sql_query = get_remote_sql(rapor_kod, params)
        if not sql_query:
            return pd.DataFrame()
        return pd.read_sql(sql_query, conn)
    except Exception as e:
        print(f"Basvuru sorgu hatasi ({rapor_kod}): {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def _normalize_basvuru_df(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["ad", "adet"])

    rename_map = {}
    for col in df.columns:
        key = str(col).strip().lower()
        if key in ("data1", "ad", "name", "tanim"):
            rename_map[col] = "ad"
        elif key in ("data2", "adet", "sayi", "count", "toplam"):
            rename_map[col] = "adet"

    out = df.rename(columns=rename_map)
    if "ad" not in out.columns or "adet" not in out.columns:
        return pd.DataFrame(columns=["ad", "adet"])

    out = out[["ad", "adet"]].copy()
    out["ad"] = out["ad"].astype(str).str.strip()
    out["adet"] = pd.to_numeric(out["adet"], errors="coerce").fillna(0)
    out = out[out["ad"].str.len() > 0]
    out.loc[out["ad"].str.lower().isin(["nan", "none", "null"]), "ad"] = "Belirtilmemiş"
    out.loc[out["ad"] == "", "ad"] = "Belirtilmemiş"
    return out.groupby("ad", as_index=False)["adet"].sum()


def _rows_from_df(df, numbered=False):
    norm = _normalize_basvuru_df(df)
    if norm.empty:
        return [], 0

    norm = norm.sort_values(["adet", "ad"], ascending=[False, True])
    rows = []
    for i, row in enumerate(norm.itertuples(index=False), start=1):
        item = {"ad": row.ad, "adet": int(row.adet)}
        if numbered:
            item["sira"] = i
        rows.append(item)
    return rows, sum(r["adet"] for r in rows)


@ttl_cache(maxsize=32, ttl=60)
def basvuru_sayilari_yukle(start_date_str, end_date_str):
    """Basvuru Sayilari sekmesi: klinik, hekim, sevk turu, brans."""
    params = _basvuru_date_params(start_date_str, end_date_str)

    df_klinik = _fetch_basvuru_df("poliklinik.basvuru_klinik_dagilim", params)
    df_hekim = _fetch_basvuru_df("poliklinik.basvuru_hekim_dagilim", params)
    df_sevk = _fetch_basvuru_df("poliklinik.basvuru_sevk_turu_dagilim", params)
    df_brans = _fetch_basvuru_df("poliklinik.basvuru_brans_dagilim", params)

    ozet_klinik, ozet_toplam = _rows_from_df(df_klinik)
    hekim, hekim_toplam = _rows_from_df(df_hekim, numbered=True)
    sevk_tur, sevk_toplam = _rows_from_df(df_sevk)
    brans, brans_toplam = _rows_from_df(df_brans)

    return {
        "ozet_klinik": ozet_klinik,
        "brans": brans,
        "sevk_tur": sevk_tur,
        "hekim": hekim,
        "ozet_toplam": ozet_toplam,
        "brans_toplam": brans_toplam,
        "sevk_toplam": sevk_toplam,
        "hekim_toplam": hekim_toplam,
    }


_BASVURU_CATEGORY_RAPOR = {
    "ozet_klinik": "poliklinik.basvuru_klinik_dagilim",
    "brans": "poliklinik.basvuru_brans_dagilim",
    "sevk_tur": "poliklinik.basvuru_sevk_turu_dagilim",
    "hekim": "poliklinik.basvuru_hekim_dagilim",
}

_MONTH_NAMES_TR = (
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
)


def _month_start(value):
    return date(value.year, value.month, 1)


def _add_months(value, months):
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def _month_ranges(end_date, month_count=6):
    first_month = _add_months(_month_start(end_date), -(month_count - 1))
    ranges = []
    for index in range(month_count):
        start = _add_months(first_month, index)
        next_start = _add_months(start, 1)
        end = next_start - timedelta(days=1)
        if index == month_count - 1:
            end = min(end, end_date)
        label = f"{_MONTH_NAMES_TR[start.month - 1]} {start.year}"
        ranges.append((start, end, label))
    return ranges


def _adet_for_name(df, ad_name):
    norm = _normalize_basvuru_df(df)
    if norm.empty:
        return 0
    target = str(ad_name or "").strip().lower()
    if not target:
        return 0
    match = norm[norm["ad"].str.strip().str.lower() == target]
    if match.empty:
        return 0
    return int(match["adet"].sum())


@ttl_cache(maxsize=128, ttl=60)
def basvuru_satir_aylik_serisi(category, ad_name, end_date_str, month_count=6):
    """Secili basvuru satiri icin son N ay adet serisi (modal grafik)."""
    rapor_kod = _BASVURU_CATEGORY_RAPOR.get(category)
    if not rapor_kod or not str(ad_name or "").strip():
        return [], []

    try:
        end_date = datetime.strptime(end_date_str[:10], "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return [], []

    month_count = max(1, min(int(month_count or 6), 6))
    labels = []
    values = []
    for start, end, label in _month_ranges(end_date, month_count):
        params = _basvuru_date_params(
            start.strftime("%Y-%m-%d"),
            end.strftime("%Y-%m-%d"),
        )
        df = _fetch_basvuru_df(rapor_kod, params)
        labels.append(label)
        values.append(_adet_for_name(df, ad_name))
    return labels, values
