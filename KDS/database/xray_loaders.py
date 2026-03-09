import pandas as pd
import streamlit as st
import pyodbc
from datetime import datetime
from .connection import get_db_connection

@st.cache_data(ttl=600, show_spinner=False)
def load_xray_analysis_data(start_date_str, end_date_str):
    
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()

    try:
       
        sql_query = f"EXEC RPR_STDS_3_1_V1 '{start_date_str}', '{end_date_str}', 'Z'"
        
        with st.spinner("Radyoloji verileri yükleniyor..."):
         
            df = pd.read_sql(sql_query, conn).copy()
            return df
    except Exception as e:
        st.error(f"??Radyoloji sorgu hatası: {e}")
        return pd.DataFrame()
    finally:
        conn.close()