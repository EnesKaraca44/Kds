import pandas as pd
from .baglanti import baglanti_olustur


def rontgen_verisi_yukle(start_date_str, end_date_str):
    conn = baglanti_olustur()
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
