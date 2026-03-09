import pandas as pd
import streamlit as st
from .connection import get_db_connection

@st.cache_data(ttl=3600, show_spinner=False)
def load_prosthetic_performance_data(start_date, end_date):
    
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()

    # ODBC Stored Procedure Çağrısı
    query = "{call RPR_STDS_4_4_V1 (?, ?, 'E', '')}"
    
    try:
        # Tarih formatlarını SQL'e uygun hale getir
        start_dt = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_dt = pd.to_datetime(end_date).strftime('%Y-%m-%d')
        
        df = pd.read_sql(query, conn, params=[start_dt, end_dt])
        
        if df is not None and not df.empty:
            # 1. Kolon isimlerini standartlaştır
            df.columns = [
                str(c).replace(' ', '_')
                     .replace('ı', 'i')
                     .replace('İ', 'I')
                     .upper() for c in df.columns
            ]

            # 2. Sayısal Kolonları Temizleme Önerisi
            # Analizde kullanılan kritik sayısal kolonları otomatik float/int formatına çevir
            numeric_cols = [
                'PLANLANANTESLIMSURESI', 'PLAN_SURE', 'HEDEF_GUN', 
                'ORTALAMA_TESLIM_SURESI', 'TESLIM_SURE_GUN', 'GERCEK_SURE'
            ]
            
            for col in numeric_cols:
                if col in df.columns:
                    # Virgüllü sayıları (12,5) nokta (12.5) formatına çevir ve sayıya dönüştür
                    if df[col].dtype == 'object':
                        df[col] = df[col].astype(str).str.replace(',', '.')
                    
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                    
                    # Yuvarlama işlemini burada yaparsak UI tarafı rahatlar
                    df[col] = df[col].round(1)

            return df
            
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"❌ SQL Veri Çekme Hatası: {e}")
        return pd.DataFrame()
    finally:
        conn.close()