import pandas as pd
from datetime import datetime
from .baglanti import baglanti_olustur
from .cache_helper import ttl_cache
from .sql_api_client import get_remote_sql


@ttl_cache(maxsize=32, ttl=600)
def tedavi_grubu_verisi_yukle(start_date_str, end_date_str):
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    try:
        sql_query = get_remote_sql(
            "tedavi_grubu.tedavi_grubu_verisi_yukle",
            {"start_date": start_date_str, "end_date": end_date_str},
        )
        if not sql_query:
            return pd.DataFrame()

        start_dt = datetime.strptime(f'{start_date_str} 00:00:00', '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(f'{end_date_str} 23:59:59', '%Y-%m-%d %H:%M:%S')

        if "?" in sql_query:
            df = pd.read_sql(sql_query, conn, params=[start_dt, end_dt])
        else:
            df = pd.read_sql(sql_query, conn)

        df['HASTA_GELIS_TARIHI'] = pd.to_datetime(df['HASTA_GELIS_TARIHI'])
        df['TETKIK_TARIHI'] = pd.to_datetime(df['TETKIK_TARIHI'])
        return df
    except Exception as e:
        print(f"Tedavi grubu verisi yuklenirken hata: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
