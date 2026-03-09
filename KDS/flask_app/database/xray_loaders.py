import pandas as pd
from .connection import get_db_connection


def load_xray_analysis_data(start_date_str, end_date_str):
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()

    try:
        sql_query = f"EXEC RPR_STDS_3_1_V1 '{start_date_str}', '{end_date_str}', 'Z'"

        df = pd.read_sql(sql_query, conn).copy()
        return df
    except Exception as e:
        print(f"❌ Radyoloji sorgu hatası: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
