import pyodbc
import streamlit as st

def get_db_connection():
    
    try:
        conn = pyodbc.connect(
            f"DRIVER={st.secrets['database']['driver']};"
            f"SERVER={st.secrets['database']['server']};"
            f"DATABASE={st.secrets['database']['database']};"
            f"UID={st.secrets['database']['username']};"
            f"PWD={st.secrets['database']['password']}"
        )
        return conn
    except Exception as e:
        st.error(f"❌ Veritabanı bağlantı hatası: {e}")
        return None