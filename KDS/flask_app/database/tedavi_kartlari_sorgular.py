import os
import warnings

import pandas as pd
from datetime import datetime
from .baglanti import baglanti_olustur
from .cache_helper import ttl_cache
from .sql_api_client import get_remote_sql


def _read_sql_pd(conn, sql_query, params=None):
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="pandas only supports SQLAlchemy connectable",
            category=UserWarning,
        )
        if params is not None:
            return pd.read_sql(sql_query, conn, params=params)
        return pd.read_sql(sql_query, conn)

# Sentinel: basarili sonuclari cache'lemek icin iç sarici kullaniyoruz.
# get_remote_sql None donerse ya da exception olursa cache'e YAZILMAZ;
# boş DataFrame cache'e kilitlenmez.
_SENTINEL = object()


def _read_sql_with_dates(conn, sql_query, start_date_str, end_date_str):
    start_dt = datetime.strptime(f"{start_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
    end_dt = datetime.strptime(f"{end_date_str} 23:59:59", "%Y-%m-%d %H:%M:%S")
    qmark_count = sql_query.count("?")

    if qmark_count <= 0:
        return _read_sql_pd(conn, sql_query)
    if qmark_count == 1:
        return _read_sql_pd(conn, sql_query, params=[start_dt])
    if qmark_count == 2:
        return _read_sql_pd(conn, sql_query, params=[start_dt, end_dt])

    params = ([start_dt, end_dt] * ((qmark_count + 1) // 2))[:qmark_count]
    return _read_sql_pd(conn, sql_query, params=params)


@ttl_cache(maxsize=64, ttl=60)
def _tedavi_gruplari_dagilimi_yukle_cached(start_date_str, end_date_str):
    """Yalnizca basarili DataFrame'i cache'ler; hata/bos durumunda sentinel doner."""
    conn = baglanti_olustur()
    if not conn:
        return _SENTINEL

    try:
        sql_query = get_remote_sql(
            "tedavi_kartlari.tedavi_gruplari_dagilimi",
            {
                "start_date": start_date_str,
                "end_date": end_date_str,
                "RECETE_GRUP_KODU": "",
                "BIRIM_ID": "",
            },
        )
        if not sql_query:
            mf = os.environ.get("RAPOR_SQL_KOD_MAP_FILE", "").strip() or "(varsayilan)"
            print(
                "[TEDAVI_KARTLARI] get_remote_sql bos dondu: "
                "tedavi_kartlari.tedavi_gruplari_dagilimi. "
                f"RAPOR_SQL_KOD_MAP_FILE={mf}"
            )
            return _SENTINEL

        return _read_sql_with_dates(conn, sql_query, start_date_str, end_date_str)
    except Exception as e:
        print(f"Tedavi kartlari dagilimi yuklenirken hata: {e}")
        return _SENTINEL
    finally:
        conn.close()


def tedavi_gruplari_dagilimi_yukle(start_date_str, end_date_str):
    result = _tedavi_gruplari_dagilimi_yukle_cached(start_date_str, end_date_str)
    if result is _SENTINEL:
        # Cache'e yazilmamis; cagiran taraf bos DataFrame alir ama bir sonraki istekte yeniden dener.
        _tedavi_gruplari_dagilimi_yukle_cached.cache_clear()
        return pd.DataFrame()
    return result


@ttl_cache(maxsize=64, ttl=60)
def _tedavi_gruplari_dagilimi_grafik_yukle_cached(start_date_str, end_date_str, recete_grup_kodu=""):
    """Yalnizca basarili DataFrame'i cache'ler; hata/bos durumunda sentinel doner."""
    conn = baglanti_olustur()
    if not conn:
        return _SENTINEL

    try:
        params = {
            "start_date": start_date_str,
            "end_date": end_date_str,
            "RECETE_GRUP_KODU": recete_grup_kodu or "",
            "BIRIM_ID": "",
        }
        sql_query = get_remote_sql("tedavi_kartlari.tedavi_gruplari_dagilimi_grafik", params)
        if not sql_query:
            mf = os.environ.get("RAPOR_SQL_KOD_MAP_FILE", "").strip() or "(varsayilan)"
            print(
                "[TEDAVI_KARTLARI] get_remote_sql bos dondu: "
                "tedavi_kartlari.tedavi_gruplari_dagilimi_grafik. "
                f"RAPOR_SQL_KOD_MAP_FILE={mf}"
            )
            return _SENTINEL

        return _read_sql_with_dates(conn, sql_query, start_date_str, end_date_str)
    except Exception as e:
        print(f"Tedavi kartlari grafik verisi yuklenirken hata: {e}")
        return _SENTINEL
    finally:
        conn.close()


def tedavi_gruplari_dagilimi_grafik_yukle(start_date_str, end_date_str, recete_grup_kodu=""):
    result = _tedavi_gruplari_dagilimi_grafik_yukle_cached(start_date_str, end_date_str, recete_grup_kodu)
    if result is _SENTINEL:
        _tedavi_gruplari_dagilimi_grafik_yukle_cached.cache_clear()
        return pd.DataFrame()
    return result
