import pandas as pd
import streamlit as st
import pyodbc
from datetime import datetime
from .connection import get_db_connection

@st.cache_data(ttl=3600, show_spinner=False)
def load_treatment_group_performance(start_date_str, end_date_str):
   
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()

    sql_query = """
        SELECT
            ISNULL(TBLTEDAVI_GRUPLARI.TEDAVI_GRUBU_ADI, 'BELİRTİLMEMİ?') AS TEDAVI_GRUBU_ADI,
            VW_HASTANE.HASTA_KODU,
            VW_HASTANE.HASTA_ADI_SOYADI,
            VW_HASTANE.HASTA_GELIS_TARIHI,
            VW_HASTANE.HASTA_GELIS_NO,
            VW_HASTANE.HASTA_KURUM_ADI,
            VW_HASTANE.TETKIK_BUTCE_KODU,
            VW_HASTANE.TETKIK_ADI,
            ISNULL(NULLIF(RntTur, 0) * SIGN(ISNULL(VW_HASTANE.radyodoktor,0))+ NULLIF(VW_HASTANE.HstTeknisyen, -32768) - VW_HASTANE.HstTeknisyen , 1) * VW_HASTANE.TETKIK_BIRIM_PUAN AS HESAPLANAN_PUAN,
            SUM(VW_HASTANE.TETKIK_TOPLAM_PUAN) AS TETKIK_TOPLAM_PUAN,
            VW_HASTANE.TETKIK_TARIHI,
            COUNT(DISTINCT CAST(VW_HASTANE.HASTA_KODU AS NVARCHAR) + CAST(VW_HASTANE.HASTA_GELIS_NO AS NVARCHAR)) AS GRUP_TOPLAM_ADET,
            SUM(VW_HASTANE.TETKIK_ADET) AS TOPLAM_ADET,
            VW_HASTANE.TETKIK_BIRIM_UCRET,
            SUM(VW_HASTANE.TETKIK_TOPLAM_UCRET) AS TETKIK_TOPLAM_UCRET,
            VW_HASTANE.TETKIK_KLINIK_ADI,
            VW_HASTANE.HASTA_CINSIYETI
        FROM
            VW_HASTANE (NOLOCK)
        LEFT OUTER JOIN
            TBLTEDAVI_GRUBU_TETKIKLERI (NOLOCK) ON VW_HASTANE.TETKIK_ID = TBLTEDAVI_GRUBU_TETKIKLERI.TETKIK_ID
        LEFT OUTER JOIN
            TBLTEDAVI_GRUPLARI (NOLOCK) ON TBLTEDAVI_GRUBU_TETKIKLERI.TEDAVI_GRUBU_ID = TBLTEDAVI_GRUPLARI.TEDAVI_GRUBU_ID
        WHERE
            1=1
            AND (VW_HASTANE.TETKIK_TARIHI BETWEEN ? AND ?)
        GROUP BY
            ISNULL(TBLTEDAVI_GRUPLARI.TEDAVI_GRUBU_ADI, 'BELİRTİLMEMİ?'),
            VW_HASTANE.HASTA_KODU,
            VW_HASTANE.HASTA_ADI_SOYADI,
            VW_HASTANE.HASTA_GELIS_TARIHI,
            VW_HASTANE.HASTA_GELIS_NO,
            VW_HASTANE.HASTA_KURUM_ADI,
            VW_HASTANE.TETKIK_BUTCE_KODU,
            VW_HASTANE.TETKIK_ADI,
            ISNULL(NULLIF(RntTur, 0) * SIGN(ISNULL(VW_HASTANE.radyodoktor,0))+ NULLIF(VW_HASTANE.HstTeknisyen, -32768) - VW_HASTANE.HstTeknisyen , 1) * VW_HASTANE.TETKIK_BIRIM_PUAN,
            VW_HASTANE.TETKIK_TARIHI,
            TBLTEDAVI_GRUPLARI.TEDAVI_GRUBU_ID,
            VW_HASTANE.TETKIK_BIRIM_UCRET,
            VW_HASTANE.TETKIK_KLINIK_ADI,
            VW_HASTANE.HASTA_CINSIYETI,
            VW_HASTANE.RntTur,
            VW_HASTANE.HstTeknisyen,
            VW_HASTANE.radyodoktor
        ORDER BY 1, 11;
    """

    try:
        start_dt = datetime.strptime(f'{start_date_str} 00:00:00', '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(f'{end_date_str} 23:59:59', '%Y-%m-%d %H:%M:%S')

        with st.spinner("Tedavi grubu analizleri hazırlanıyor..."):
            df = pd.read_sql(sql_query, conn, params=[start_dt, end_dt])
            
           
            df['HASTA_GELIS_TARIHI'] = pd.to_datetime(df['HASTA_GELIS_TARIHI'])
            df['TETKIK_TARIHI'] = pd.to_datetime(df['TETKIK_TARIHI'])
            return df
    except Exception as e:
        st.error(f"??Tedavi grubu verisi yüklenirken hata: {e}")
        return pd.DataFrame()
    finally:
        conn.close()