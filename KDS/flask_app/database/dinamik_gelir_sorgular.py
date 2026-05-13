import pandas as pd
from datetime import datetime
from .baglanti import baglanti_olustur
from .sql_api_client import get_remote_sql


def son_fatura_metrikleri_getir(fatura_no):
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    try:
        fatura_no_param = str(fatura_no).strip()
        if not fatura_no_param:
            return pd.DataFrame()

        sql = get_remote_sql(
            "dinamik_gelir.son_fatura_metrikleri_getir",
            {"FATURA_NO": fatura_no_param},
        )
        if not sql:
            return pd.DataFrame()

        df = pd.read_sql(sql, conn)
        if 'FATURA_NO' in df.columns:
            df['FATURA_NO'] = df['FATURA_NO'].apply(lambda x: str(int(float(x))))
        return df
    except Exception as e:
        print(f"SQL Hatası: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def dinamik_dashboard_metrikleri_getir(start_date_str, end_date_str):
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    try:
        sql = get_remote_sql(
            "dinamik_gelir.dinamik_dashboard_metrikleri_getir",
            {"start_date": start_date_str, "end_date": end_date_str},
        )
        if not sql:
            return pd.DataFrame()

        start_dt = datetime.strptime(f"{start_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
        end_dt_param = datetime.strptime(f"{end_date_str}", "%Y-%m-%d")

        if "?" in sql:
            df = pd.read_sql(sql, conn, params=[start_dt, end_dt_param, start_dt, end_dt_param])
        else:
            df = pd.read_sql(sql, conn)

        df['FATURA_NO'] = 'Canlı Veri'
        return df
    except Exception as e:
        print(f"SQL Hatası (Dinamik Dashboard): {e}")
        return pd.DataFrame()
    finally:
        conn.close()
