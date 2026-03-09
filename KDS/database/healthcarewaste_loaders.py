import pandas as pd
import streamlit as st
import pyodbc
from datetime import datetime
from .connection import get_db_connection

@st.cache_data(ttl=3600, show_spinner=False)
def load_medical_waste_data(start_date_str, end_date_str):
   
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()

  
    sql_query = f"EXEC RPR_STDS_15_5_V1 '{start_date_str}', '{end_date_str}', NULL, 'A'"

    try:
        with st.spinner("Tıbbi atık verileri analiz ediliyor..."):
            df = pd.read_sql_query(sql_query, conn)
            return df
    except Exception as e:
        st.error(f"❌ Tıbbi atık verisi yüklenirken hata: {e}")
        return pd.DataFrame()
    finally:
        conn.close()