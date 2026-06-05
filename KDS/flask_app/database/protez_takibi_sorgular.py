import warnings

import pandas as pd
from .baglanti import baglanti_olustur
from .cache_helper import ttl_cache
from .sql_api_client import get_remote_sql


def _normalize_broken_null_literals(sql: str) -> str:
    """
    Bazi Rapor API SQL'lerinde bos parametreler 'NULL' (string) olarak geliyor.
    Bu durum ozellikle CAST('NULL' AS DATE) gibi ifadelerde sorguyu bozuyor.
    """
    if not isinstance(sql, str) or not sql:
        return sql

    normalized = sql.replace("'NULL'", "NULL")
    normalized = normalized.replace("'null'", "NULL")
    return normalized


def _normalize_asama_sql(sql: str) -> str:
    """ASAMA_GIRILMEMIS sablonundaki yanlis kolon adini duzeltir (ISLEM_TRH -> ISTSH_TRH)."""
    sql = _normalize_broken_null_literals(sql)
    if not isinstance(sql, str) or not sql:
        return sql
    return sql.replace("shh.ISLEM_TRH", "shh.ISTSH_TRH")


def _read_sql_with_optional_params(conn, sql, qmark_value=""):
    """
    API'den gelen sorgularda bazen ODBC '?' parametreleri kalabiliyor.
    - '?' yoksa direkt calistir.
    - Varsa, tum '?' icin ayni degeri gonder.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="pandas only supports SQLAlchemy connectable",
            category=UserWarning,
        )
        qmarks = sql.count("?")
        if qmarks == 0:
            return pd.read_sql(sql, conn)
        return pd.read_sql(sql, conn, params=tuple([qmark_value] * qmarks))


@ttl_cache(maxsize=32, ttl=60)
def asama_girilmemis_hasta_listesi_yukle(hizmet_sut_kodu=None, islem_tarihi=None, birim_id=None):
    """
    Asama girilmemis hasta listesini getirir.
    - hizmet_sut_kodu: ilgili SUT kodu (opsiyonel)
    - islem_tarihi: YYYY-MM-DD formatinda tarih (opsiyonel)
    - birim_id: servis birim id (opsiyonel)
    """
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    try:
        sql = get_remote_sql(
            "protez_takibi.asama_girilmemis_hasta_listesi_yukle",
            {
                "SUT_KODU": hizmet_sut_kodu or "",
                "ISLEM_TARIHI": islem_tarihi or "",
                "BIRIM_ID": birim_id or "",
            },
        )
        if not sql:
            return pd.DataFrame()
        sql = _normalize_asama_sql(sql)
        return _read_sql_with_optional_params(conn, sql, hizmet_sut_kodu or "")
    except Exception as e:
        print(f"Asama girilmemis hasta listesi hatasi: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


@ttl_cache(maxsize=32, ttl=60)
def protez_suresi_gecen_hasta_birim_yukle(birim_id_csv=None):
    """
    Protez suresi gecen hasta/birim listesini getirir.
    - birim_id_csv: '12,13,14' gibi CSV birim id listesi (opsiyonel)
    """
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    try:
        sql = get_remote_sql(
            "protez_takibi.protez_suresi_gecen_hasta_birim_yukle",
            {"BIRIM_ID": birim_id_csv or ""},
        )
        if not sql:
            return pd.DataFrame()
        sql = _normalize_broken_null_literals(sql)
        return _read_sql_with_optional_params(conn, sql, "")
    except Exception as e:
        print(f"Protez suresi gecen hasta/birim hatasi: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
