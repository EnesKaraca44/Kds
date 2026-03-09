import pandas as pd
from datetime import datetime
from .connection import get_db_connection


def load_appointment_data(start_date_str, end_date_str):
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()

    sql_query = """
        SELECT
            TblRandevular.RanID AS RandevuID,
            TblRandevular.BsvTrh, TblRandevular.Trh, TblRandevular.Saat,
            TblRandevular.HstKod, TblRandevular.DktID, TblRandevular.PolID,
            TblRandevular.M_RANDEVU_DURUM, TblRandevular.TC_KIMLIK_NO,
            TblRandevular.RANDEVU_TURU_ID, TblRandevular.M_RANDEVU_EKLEYEN,
            TblRandevular.IPTAL,
            DATEDIFF(DAY, TblRandevular.BsvTrh, ISNULL(TblRandevular.Trh, GETDATE())) AS fark,
            TBLRANDEVU_TURU.RANDEVU_TURU_ADI, TblServis.SrvAd,
            ISNULL(TblDoktor.DktAd, 'BELİRTİLMEMİŞ') AS dktad,
            TBLHASTA.HstCepTel, TBLHASTA.hsttel1 AS tlfno,
            CASE
                WHEN TblRandevular.M_RANDEVU_DURUM = 1 THEN 'Geldi'
                WHEN TblRandevular.M_RANDEVU_DURUM = 2 AND sv.sevk_Saat1 IS NULL THEN 'Gelmedi'
                WHEN TblRandevular.M_RANDEVU_DURUM = 2 AND sv.sevk_Saat1 IS NOT NULL THEN 'Geç Geldi'
                WHEN sv.sevk_Saat1 IS NOT NULL THEN 'Geldi'
                WHEN TblRandevular.M_RANDEVU_DURUM = 3 THEN 'Belirsiz'
                ELSE 'Gelmedi'
            END AS Durum,
            TBLRANDEVU_TURU.RANDEVU_TURU_GUN_LIMIT,
            CASE
                WHEN ISNULL(MHRS_RANDEVU_TUR.ad, 'BELİRTİLMEMİŞ') = 'BELİRTİLMEMİŞ' THEN 'RS'
                ELSE ISNULL(MHRS_RANDEVU_TUR.ad, 'BELİRTİLMEMİŞ')
            END AS Randevuverilme_Yeri
        FROM
            TblRandevular (NOLOCK)
            LEFT JOIN TBLRANDEVU_TURU (NOLOCK) ON TblRandevular.RANDEVU_TURU_ID = TBLRANDEVU_TURU.RANDEVU_TURU_ID
            LEFT JOIN TblServis (NOLOCK) ON TblRandevular.PolID = TblServis.SrvNo
            LEFT JOIN TblDoktor (NOLOCK) ON TblRandevular.DktID = TblDoktor.DktNo
            LEFT JOIN TBLHASTA (NOLOCK) ON (TBLHASTA.HstNufus = NULLIF(TblRandevular.TC_KIMLIK_NO, '0'))
            LEFT JOIN MHRS_RANDEVU_TUR (NOLOCK) ON TblRandevular.M_RANDEVU_EKLEYEN = MHRS_RANDEVU_TUR.kod
            LEFT JOIN (
                SELECT
                    MIN(sevk_Saat1) AS sevk_Saat1, sevk_Hasta_kodu,
                    CAST(FLOOR(CAST(tblsevk.sevk_etme_trh AS FLOAT)) AS DATETIME) AS sevk_etme_trh
                FROM tblsevk (NOLOCK)
                GROUP BY sevk_Hasta_kodu, CAST(FLOOR(CAST(tblsevk.sevk_etme_trh AS FLOAT)) AS DATETIME)
            ) AS sv ON TblRandevular.Trh = sv.sevk_etme_trh AND TblRandevular.HstKod = sv.sevk_Hasta_kodu
        WHERE
            TblRandevular.IPTAL = 0
            AND (TblRandevular.Trh BETWEEN ? AND ?)
            AND (TblRandevular.RANDEVU_TURU_ID IN (6,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44))
    """

    try:
        start_dt = datetime.strptime(f'{start_date_str} 00:00:00', '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(f'{end_date_str} 23:59:59', '%Y-%m-%d %H:%M:%S')

        df = pd.read_sql(sql_query, conn, params=[start_dt, end_dt])
        df['BsvTrh'] = pd.to_datetime(df['BsvTrh'])
        df['Trh'] = pd.to_datetime(df['Trh'])
        return df
    except Exception as e:
        print(f"❌ Randevu verisi yüklenirken hata: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
