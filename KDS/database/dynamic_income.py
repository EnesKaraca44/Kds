import pandas as pd
import streamlit as st
from .connection import get_db_connection

def get_latest_fatura_metrics(): 
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()

    sql = """
        SELECT 
            FATURA_NO,
            COUNT(*) AS ToplamHasta, 
            SUM(HASTA_TOPLAM_TUTAR) AS ToplamTutar
        FROM TBLFATURAHASTA
        WHERE FATURA_NO = 2026000005
        AND HASTA_KURUM_TURU_ID IN (1,2,3,4,5)
        GROUP BY FATURA_NO;
    """
    try:
        df = pd.read_sql(sql, conn)
        df['FATURA_NO'] = df['FATURA_NO'].apply(lambda x: str(int(float(x))))
        return df
    except Exception as e:
        st.error(f"SQL Hatası: {e}")
        return pd.DataFrame()
    finally:
        conn.close()