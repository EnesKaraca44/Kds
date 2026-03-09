import pandas as pd
from datetime import datetime
from .connection import get_db_connection


def load_performance_revenue_data(start_date_str, end_date_str, test_type_filter_clause=""):
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()

    sql_query = f"""
        SELECT
            VW_HASTANE.TETKIK_DOKTOR_ADI,
            VW_HASTANE.TETKIK_ADI,
            CAST(VW_HASTANE.TETKIK_TARIHI AS DATE) AS TETKIK_GUNLUK_TARIH,
            SUM(VW_HASTANE.TETKIK_ADET) AS Toplam_Adet,
            SUM(VW_HASTANE.TETKIK_ADET * VW_HASTANE.TETKIK_BIRIM_UCRET) AS Toplam_Gelir,
            SUM(
                VW_HASTANE.TETKIK_ADET *
                (ISNULL(NULLIF(RntTur, 0) * SIGN(isnull(VW_HASTANE.radyodoktor,0))+ NULLIF(VW_HASTANE.HstTeknisyen, -32768) - VW_HASTANE.HstTeknisyen , 1) * VW_HASTANE.TETKIK_BIRIM_PUAN)
            ) AS Toplam_Puan
        FROM
            VW_HASTANE (NOLOCK)
            INNER JOIN TblDoktor (Nolock) ON VW_HASTANE.TETKIK_DOKTOR_ID = TblDoktor.DktNo
            LEFT JOIN (SELECT DktNo,DktAd From TblDoktor (Nolock)) AS Kons ON VW_HASTANE.T_DOKTOR2_ID=Kons.Dktno
        WHERE
            VW_HASTANE.TETKIK_BIRIM_PUAN > 0
            AND VW_HASTANE.TETKIK_ADET > 0
            AND VW_HASTANE.TETKIK_TARIHI BETWEEN ? AND ?
            {test_type_filter_clause}
        GROUP BY
            VW_HASTANE.TETKIK_DOKTOR_ADI,
            VW_HASTANE.TETKIK_ADI,
            CAST(VW_HASTANE.TETKIK_TARIHI AS DATE)
        ORDER BY 1, 2, 3;
    """

    try:
        start_dt = datetime.strptime(f'{start_date_str} 00:00:00', '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(f'{end_date_str} 23:59:59', '%Y-%m-%d %H:%M:%S')

        df = pd.read_sql(sql_query, conn, params=[start_dt, end_dt])
        df['TETKIK_GUNLUK_TARIH'] = pd.to_datetime(df['TETKIK_GUNLUK_TARIH'])
        return df
    except Exception as e:
        print(f"❌ Finansal veri yükleme hatası: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
