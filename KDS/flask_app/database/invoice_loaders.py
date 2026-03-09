import pandas as pd
from datetime import datetime
from .connection import get_db_connection


def load_invoice_revenue_data(start_date_str, end_date_str):
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()

    sql_query = """
        SELECT
            F.FATURA_NO,
            F.FATURA_TARIHI,
            '(' + LTRIM(CAST(F.FATURA_KURUM_ID AS NVARCHAR(MAX))) + ') ' + F.FATURA_ILGILI AS FATURA_ILGILI,
            KT.tad AS KURUM_TURU,
            F.FATURA_TOPLAM_TUTAR,
            F.FATURA_KISI_SAYISI,
            F.FATURA_ACIKLAMA,
            F.FATURA_TOPLAM_KDV,
            F.FATURA_TOPLAM_KDV + F.FATURA_TOPLAM_TUTAR AS FATURA_KDVLI_TOPLAM_TUTAR
        FROM
            TBLFATURA F (NOLOCK)
        INNER JOIN
            TblKurum K (NOLOCK) ON F.FATURA_KURUM_ID = K.KrmKodu
        INNER JOIN
            TblKurumTur KT (NOLOCK) ON K.KrmSecim = KT.tkod
        WHERE
            F.FATURA_TARIHI BETWEEN ? AND ? 
            AND F.FATURA_TURU <= 2
        ORDER BY
            KT.tad, F.FATURA_ILGILI, F.FATURA_NO;
    """

    try:
        start_dt = datetime.strptime(f'{start_date_str} 00:00:00', '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(f'{end_date_str} 23:59:59', '%Y-%m-%d %H:%M:%S')

        df = pd.read_sql(sql_query, conn, params=[start_dt, end_dt])
        if not df.empty:
            df['FATURA_TARIHI'] = pd.to_datetime(df['FATURA_TARIHI'])
        return df
    except Exception as e:
        print(f"❌ Kurum gelir verisi yüklenirken hata: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
