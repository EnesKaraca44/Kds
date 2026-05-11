import pandas as pd
from .baglanti import baglanti_olustur
from .cache_helper import ttl_cache
from .sql_api_client import get_remote_sql


@ttl_cache(maxsize=32, ttl=600)
def randevu_verisi_yukle(start_date_str, end_date_str):
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    try:
        sql = get_remote_sql(
            "randevu.randevu_verisi_yukle",
            {"start_date": start_date_str, "end_date": end_date_str},
        )
        if not sql:
            return pd.DataFrame()

        df = pd.read_sql(sql, conn)
        df['BsvTrh'] = pd.to_datetime(df['BsvTrh'])
        df['Trh'] = pd.to_datetime(df['Trh'])
        return df
    except Exception as e:
        print(f"Randevu verisi yuklenirken hata: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
