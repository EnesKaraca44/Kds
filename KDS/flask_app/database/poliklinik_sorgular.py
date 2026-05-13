import pandas as pd
from datetime import datetime
from .baglanti import baglanti_olustur
from .cache_helper import ttl_cache
from .sql_api_client import get_remote_sql


@ttl_cache(maxsize=32, ttl=600)
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
