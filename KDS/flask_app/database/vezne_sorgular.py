import pandas as pd
from datetime import datetime

from .baglanti import baglanti_olustur
from .cache_helper import ttl_cache
from .sql_api_client import get_remote_sql


@ttl_cache(maxsize=32, ttl=600)
def kasa_ozet_verisi_yukle(start_date_str: str, end_date_str: str) -> pd.DataFrame:
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    try:
        sql = get_remote_sql(
            "vezne.kasa_ozet_verisi_yukle",
            {"start_date": start_date_str, "end_date": end_date_str},
        )
        if not sql:
            return pd.DataFrame()

        if "?" in sql:
            start_dt = datetime.strptime(f"{start_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(f"{end_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
            return pd.read_sql(sql, conn, params=[start_dt, end_dt])

        return pd.read_sql(sql, conn)
    except Exception as e:
        print(f"❌ Vezne kasa özet verisi yüklenirken hata: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


@ttl_cache(maxsize=32, ttl=600)
def kasa_hareket_turu_verisi_yukle(start_date_str: str, end_date_str: str, kasa_id: int) -> pd.DataFrame:
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    try:
        sql = get_remote_sql(
            "vezne.kasa_hareket_turu_verisi_yukle",
            {"start_date": start_date_str, "end_date": end_date_str, "kasa_id": int(kasa_id)},
        )
        if not sql:
            return pd.DataFrame()

        if "?" in sql:
            start_dt = datetime.strptime(f"{start_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(f"{end_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
            return pd.read_sql(sql, conn, params=[int(kasa_id), start_dt, end_dt])

        return pd.read_sql(sql, conn)
    except Exception as e:
        print(f"❌ Vezne hareket türü verisi yüklenirken hata: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


@ttl_cache(maxsize=32, ttl=600)
def kasa_aylik_verisi_yukle(start_date_str: str, end_date_str: str, kasa_id: int) -> pd.DataFrame:
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    try:
        sql = get_remote_sql(
            "vezne.kasa_aylik_verisi_yukle",
            {"start_date": start_date_str, "end_date": end_date_str, "kasa_id": int(kasa_id)},
        )
        if not sql:
            return pd.DataFrame()

        if "?" in sql:
            start_dt = datetime.strptime(f"{start_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(f"{end_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
            return pd.read_sql(sql, conn, params=[start_dt, int(kasa_id), start_dt, end_dt])

        return pd.read_sql(sql, conn)
    except Exception as e:
        print(f"❌ Vezne aylık verisi yüklenirken hata: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

