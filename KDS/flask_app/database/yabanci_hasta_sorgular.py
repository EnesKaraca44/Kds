import pandas as pd
from datetime import datetime
from .baglanti import baglanti_olustur
from .cache_helper import ttl_cache
from .sql_api_client import get_remote_sql


@ttl_cache(maxsize=32, ttl=600)
def yabanci_hasta_verisi_yukle(start_date_str, end_date_str):
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    try:
        sql = get_remote_sql(
            "yabanci_hasta.yabanci_hasta_verisi_yukle",
            {"start_date": start_date_str, "end_date": end_date_str},
        )
        if not sql:
            return pd.DataFrame()

        if "?" in sql:
            start_dt = datetime.strptime(f'{start_date_str} 00:00:00', '%Y-%m-%d %H:%M:%S')
            end_dt = datetime.strptime(f'{end_date_str} 23:59:59', '%Y-%m-%d %H:%M:%S')
            df = pd.read_sql(sql, conn, params=[start_dt, end_dt])
        else:
            df = pd.read_sql(sql, conn)

        if not df.empty:
            df['hstgtrh'] = pd.to_datetime(df['hstgtrh'], errors='coerce')
            df['HstDtrh'] = pd.to_datetime(df['HstDtrh'], errors='coerce')

            current_year = datetime.now().year
            df['YAS'] = (current_year - df['HstDtrh'].dt.year).astype('Int64')
            df = df.drop(columns=['HstDtrh'])

        return df
    except Exception as e:
        print(f"Yabanci hasta verisi hatasi: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
