import pandas as pd
from .connection import get_db_connection


def load_prosthetic_performance_data(start_date, end_date):
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()

    query = "{call RPR_STDS_4_4_V1 (?, ?, 'E', '')}"

    try:
        start_dt = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_dt = pd.to_datetime(end_date).strftime('%Y-%m-%d')

        df = pd.read_sql(query, conn, params=[start_dt, end_dt])

        if df is not None and not df.empty:
            df.columns = [
                str(c).replace(' ', '_')
                     .replace('ı', 'i')
                     .replace('İ', 'I')
                     .upper() for c in df.columns
            ]

            numeric_cols = [
                'PLANLANANTESLIMSURESI', 'PLAN_SURE', 'HEDEF_GUN',
                'ORTALAMA_TESLIM_SURESI', 'TESLIM_SURE_GUN', 'GERCEK_SURE'
            ]

            for col in numeric_cols:
                if col in df.columns:
                    if df[col].dtype == 'object':
                        df[col] = df[col].astype(str).str.replace(',', '.')
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                    df[col] = df[col].round(1)

            return df

        return pd.DataFrame()

    except Exception as e:
        print(f"❌ SQL Veri Çekme Hatası: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
