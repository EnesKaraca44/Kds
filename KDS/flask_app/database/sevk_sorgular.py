import pandas as pd
from .baglanti import baglanti_olustur
from .cache_helper import ttl_cache


@ttl_cache(maxsize=32, ttl=600)
def sevk_verisi_yukle(start_date_str, end_date_str):
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    start_dt = f"{start_date_str} 00:00:00"
    end_dt = f"{end_date_str} 23:59:59"
    start_date_only = start_date_str
    end_date_only = end_date_str

    sql_query = """
    WITH Hasta AS (
        SELECT 
            ISNULL(Doktor.DktAd,'BELİRTİLMEMİŞ') AS DOKTOR_ADI,
            tbpd.HstKod
        FROM TblPolDefterDoktor tbpd (NOLOCK)
        LEFT JOIN TblDoktor Doktor ON tbpd.DoktorID = Doktor.DktNo
        LEFT JOIN TblHastaRO thr ON thr.HstKod = tbpd.HstKod 
            AND thr.HstSra = tbpd.HstGelisNo 
            AND thr.HstGtrh = tbpd.HstGelisTrh
        WHERE ISNULL(thr.HstSilindi,0)=0
          AND tbpd.Trh BETWEEN ? AND ?
          AND ((ISNULL(tbpd.ID_FLAG,2) & 6) IN (2,4,6))
        UNION ALL
        SELECT 
            ISNULL(Doktor.DktAd,'BELİRTİLMEMİŞ'),
            tbpd.HstKod
        FROM TblPolDefter tbpd (NOLOCK)
        LEFT JOIN TblDoktor Doktor ON tbpd.DoktorID = Doktor.DktNo
        LEFT JOIN TblHastaRO thr ON thr.HstKod = tbpd.HstKod 
            AND thr.HstSra = tbpd.HstGelisNo 
            AND thr.HstGtrh = tbpd.HstGelisTrh
        WHERE ISNULL(thr.HstSilindi,0)=0
          AND tbpd.Trh BETWEEN ? AND ?
          AND ((ISNULL(tbpd.ID_FLAG,2) & 6) IN (2,4,6))
    ),
    Sevk AS (
        SELECT
            td.DktAd AS DOKTOR_ADI,
            ed.DktAd AS Sevk_Eden_Doktor_Ad,
            se.SrvAd AS Sevk_Eden_Srv_Ad,
            td.DktAd AS Sevk_Kabul_Doktor_Ad,
            tp.SrvAd AS Sevk_Kabul_Srv_Ad,
            CAST(s.Sevk_Etme_Trh AS DATE) AS Sevk_Tarihi,
            COUNT(DISTINCT s.Sevk_Hasta_Gels_No) AS TOPLAM_SEVK
        FROM tblsevk AS s (NOLOCK)
        LEFT JOIN TblDoktor ed ON ed.DktNo = s.Sevk_Eden_Doktor
        LEFT JOIN TblDoktor td ON td.DktNo = s.Sevk_Kabul_Doktor
        LEFT JOIN tblservis se ON se.SrvNo = s.Sevk_Eden_Srv
        LEFT JOIN tblservis tp ON tp.SrvNo = s.Sevk_Kabul_Srv
        WHERE s.sevk_Turu = 2
          AND s.Sevk_Etme_Trh BETWEEN ? AND ?
          AND tp.SrvAd <> 'RÖNTGEN KLİNİĞİ'
        GROUP BY
            td.DktAd, ed.DktAd, se.SrvAd, tp.SrvAd, CAST(s.Sevk_Etme_Trh AS DATE)
    )
    SELECT 
        ISNULL(h.DOKTOR_ADI, s.DOKTOR_ADI) AS DOKTOR_ADI,
        ISNULL(h.TOPLAM_HASTA,0) AS TOPLAM_HASTA,
        ISNULL(s.TOPLAM_SEVK,0) AS TOPLAM_SEVK,
        s.Sevk_Eden_Doktor_Ad,
        s.Sevk_Eden_Srv_Ad,
        s.Sevk_Kabul_Doktor_Ad,
        s.Sevk_Kabul_Srv_Ad,
        s.Sevk_Tarihi
    FROM (
        SELECT DOKTOR_ADI, COUNT(DISTINCT HstKod) AS TOPLAM_HASTA
        FROM Hasta
        GROUP BY DOKTOR_ADI
    ) h
    FULL OUTER JOIN Sevk s ON h.DOKTOR_ADI = s.DOKTOR_ADI
    """

    try:
        params = [start_date_only, end_date_only, start_date_only, end_date_only, start_dt, end_dt]
        df = pd.read_sql(sql_query, conn, params=params)
        return df
    except Exception as e:
        print(f"❌ SQL Hatası: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
