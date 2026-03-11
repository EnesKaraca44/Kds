import pandas as pd
from .baglanti import baglanti_olustur


def tibbi_atik_verisi_yukle(start_date_str, end_date_str):
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    sql_query = f"EXEC RPR_STDS_15_5_V1 '{start_date_str}', '{end_date_str}', NULL, 'A'"

    try:
        df = pd.read_sql_query(sql_query, conn)
        return df
    except Exception as e:
        print(f"❌ Tıbbi atık verisi yüklenirken hata: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
