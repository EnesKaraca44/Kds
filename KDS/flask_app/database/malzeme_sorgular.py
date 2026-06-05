import pandas as pd
from datetime import datetime
from .baglanti import baglanti_olustur
from .cache_helper import ttl_cache
from .sql_api_client import get_remote_sql


# Rapor API / SQL Server kolon adlari camelCase route ile uyusmayabiliyor.
# Anahtar: kucuk harf + alt cizgi (bosluk da alt cizgiye cevrilir).
_MALZEME_TUKETIM_COL_KEYS = {
    "dusumtarih": "dusumTarih",
    "dusum_tarih": "dusumTarih",
    "dusum_tarihi": "dusumTarih",
    "dusumtrh": "dusumTarih",
    "cikistarih": "dusumTarih",
    "cikis_tarih": "dusumTarih",
    "dusummiktar": "dusumMiktar",
    "dusum_miktar": "dusumMiktar",
    "dusummiktari": "dusumMiktar",
    "cikismiktar": "dusumMiktar",
    "cikis_miktar": "dusumMiktar",
    "hastaadsoyad": "hastaAdSoyad",
    "hasta_ad_soyad": "hastaAdSoyad",
    "stokad": "stokAd",
    "stok_ad": "stokAd",
    "malzemeadi": "stokAd",
    "bransadi": "bransAdi",
    "brans_adi": "bransAdi",
    "doktoradsoyad": "doktorAdSoyad",
    "doktor_ad_soyad": "doktorAdSoyad",
    "hekimadsoyad": "doktorAdSoyad",
    "tetkikadi": "tetkikAdi",
    "tetkik_adi": "tetkikAdi",
    "islemtanim": "tetkikAdi",
    "toplam": "toplam",
    "toplamtutar": "toplam",
    "tutar": "toplam",
}


def _normalize_malzeme_tuketim_columns(df: pd.DataFrame) -> pd.DataFrame:
    """API'den gelen DataFrame kolonlarini malzeme route'unun bekledigi isimlere donusturur."""
    if df is None or df.empty:
        return df
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    rename = {}
    targets_used = set()
    for col in list(out.columns):
        key = col.lower().replace(" ", "_")
        canonical = _MALZEME_TUKETIM_COL_KEYS.get(key)
        if not canonical:
            continue
        if col == canonical:
            targets_used.add(canonical)
            continue
        if canonical in targets_used:
            continue
        if canonical in out.columns and col != canonical:
            continue
        rename[col] = canonical
        targets_used.add(canonical)
    if rename:
        out = out.rename(columns=rename)
    return out


def _safe_read_sql(conn, sql: str, param_candidates):
    """
    SQL'de ? placeholder varsa farklı parametre kombinasyonlarını sırayla dener.
    Bazı ortamlarda aynı rapor SQL'i farklı sayıda ? ile dönebiliyor.
    """
    qmark_count = sql.count("?")
    if qmark_count <= 0:
        return pd.read_sql(sql, conn)

    last_err = None
    for candidate in param_candidates:
        if candidate is None:
            continue
        try:
            params = tuple(candidate)
            if qmark_count != len(params):
                continue
            return pd.read_sql(sql, conn, params=params)
        except Exception as exc:
            last_err = exc
            continue

    # Son çare: ilk adayın uzunluğunu qmark sayısına zorlayıp tekrar dene.
    if param_candidates:
        base = list(param_candidates[0] or [])
        if base:
            if len(base) < qmark_count:
                repeat = (qmark_count + len(base) - 1) // len(base)
                base = (base * repeat)[:qmark_count]
            else:
                base = base[:qmark_count]
            return pd.read_sql(sql, conn, params=tuple(base))

    if last_err:
        raise last_err
    return pd.read_sql(sql, conn)


def _parse_miad_dates(series: pd.Series) -> pd.Series:
    """
    shVadeTarih farkli formatlarda gelebilir:
    - datetime/string
    - YYYYMMDD sayisal metin
    Varsayilan to_datetime sayisal degeri unix epoch gibi yorumlayip 1970'e cekebilir.
    """
    if series is None or series.empty:
        return series

    raw = series.astype(str).str.strip()
    numeric_8 = raw.str.fullmatch(r"\d{8}")

    parsed = pd.to_datetime(series, errors="coerce")
    if numeric_8.any():
        parsed_yyyymmdd = pd.to_datetime(raw.where(numeric_8), format="%Y%m%d", errors="coerce")
        parsed = parsed.where(~numeric_8, parsed_yyyymmdd)
    return parsed


@ttl_cache(maxsize=32, ttl=60)
def malzeme_tuketim_verisi_yukle(start_date_str, end_date_str):
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    try:
        sql = get_remote_sql(
            "malzeme.malzeme_tuketim_verisi_yukle",
            {"start_date": start_date_str, "end_date": end_date_str},
        )
        if not sql:
            return pd.DataFrame()

        start_dt = datetime.strptime(f'{start_date_str} 00:00:00', '%Y-%m-%d %H:%M:%S')
        end_dt_param = datetime.strptime(f'{end_date_str}', '%Y-%m-%d')

        df = _safe_read_sql(
            conn,
            sql,
            [
                (start_dt, end_dt_param),
                (start_dt, end_dt_param, start_dt, end_dt_param),
                (start_date_str, end_date_str),
                (start_date_str, end_date_str, start_date_str, end_date_str),
            ],
        )

        df = _normalize_malzeme_tuketim_columns(df)

        if not df.empty and "dusumTarih" not in df.columns:
            print(f"UYARI: malzeme_tuketim — dusumTarih yok. Kolonlar: {list(df.columns)}")

        if not df.empty and 'dusumTarih' in df.columns:
            df['dusumTarih'] = pd.to_datetime(df['dusumTarih'])
        return df
    except Exception as e:
        print(f"Stock data loading error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


@ttl_cache(maxsize=8, ttl=3600)
def depo_birim_liste_yukle():
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    try:
        sql = get_remote_sql("malzeme.depo_birim_liste_yukle")
        if not sql:
            return pd.DataFrame()

        return pd.read_sql(sql, conn)
    except Exception as e:
        print(f"Depo birim liste yukleme hatasi: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


@ttl_cache(maxsize=32, ttl=60)
def depo_mevcut_verisi_yukle(start_date_str, end_date_str, birim_id=None, birim_id_list=None):
    """Depo mevcut stok ve miad verisi — Kategori 6 & 7 icin.
    birim_id: tek depo secimi
    birim_id_list: tum depolarin ID listesi (Tum Depolar icin)
    """
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    try:
        # birim_id: tek ID, birim_id_list: birden fazla ID virgülle ayrılmış string olarak geçilir
        if birim_id:
            birim_id_param = str(int(birim_id))
        elif birim_id_list:
            birim_id_param = ','.join(str(int(x)) for x in birim_id_list)
        else:
            birim_id_param = ""

        sql = get_remote_sql(
            "malzeme.depo_mevcut_verisi_yukle",
            {
                "start_date": start_date_str,
                "end_date": end_date_str,
                "BIRIM_ID": birim_id_param,
            },
        )
        if not sql:
            return pd.DataFrame()

        start_dt = datetime.strptime(f"{start_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(f"{end_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
        df = _safe_read_sql(
            conn,
            sql,
            [
                (start_dt, end_dt, birim_id_param),
                (start_date_str, end_date_str, birim_id_param),
                (start_dt, end_dt, birim_id_param, birim_id_param),
                (start_date_str, end_date_str, birim_id_param, birim_id_param),
                (start_dt, end_dt),
                (start_date_str, end_date_str),
                (birim_id_param,),
            ],
        )

        if not df.empty and 'shVadeTarih' in df.columns:
            df['shVadeTarih'] = _parse_miad_dates(df['shVadeTarih'])

        for col in ('shMiktar', 'shMevcutMiktar', 'shCikisMiktar',
                     'kritikStokMiktar', 'minStokMiktar', 'maxStokMiktar'):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        return df
    except Exception as e:
        print(f"Depo mevcut veri yukleme hatasi: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
