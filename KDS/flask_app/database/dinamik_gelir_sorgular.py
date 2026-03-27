import pandas as pd
from datetime import datetime
from .baglanti import baglanti_olustur


def son_fatura_metrikleri_getir():
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    sql = """
        SELECT 
            FATURA_NO,
            COUNT(*) AS ToplamHasta, 
            SUM(HASTA_TOPLAM_TUTAR) AS ToplamTutar
        FROM TBLFATURAHASTA
        WHERE FATURA_NO = 2026000005
        AND HASTA_KURUM_TURU_ID IN (1,2,3,4,5)
        GROUP BY FATURA_NO;
    """
    try:
        df = pd.read_sql(sql, conn)
        df['FATURA_NO'] = df['FATURA_NO'].apply(lambda x: str(int(float(x))))
        return df
    except Exception as e:
        print(f"SQL Hatası: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def dinamik_dashboard_metrikleri_getir(start_date_str, end_date_str):
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    sql = """
    SELECT 
        (SELECT COUNT( sks.SEVK_HST_GELIS_ID) 
         FROM SBS_KLINIK_SEVK sks WITH(NOLOCK) 
         INNER JOIN SBS_HASTA_RESMI_UCRETLI hru WITH(NOLOCK) ON sks.SEVK_HST_GELIS_ID = hru.HST_GELIS_ID AND ISNULL(hru.PSF_ID,0) = 0
         INNER JOIN SBS_HASTA as h WITH(NOLOCK) ON h.HASTA_KIMLIK_ID = sks.HASTA_KIMLIK_ID AND ISNULL(h.PSF_ID,0) = 0 
         INNER JOIN BIRIM as b WITH(NOLOCK) ON b.BIRIM_ID = sks.SEVK_EDILEN_KLINIK_BIRIM_ID AND ISNULL(b.PSF_ID,0) = 0 
         LEFT JOIN SBS_DOKTOR as hkmk WITH(NOLOCK) ON hkmk.KIMLIK_ID = sks.SEVK_EDILEN_HEKIM_KIMLIK_ID AND ISNULL(hkmk.PSF_ID,0) = 0 
         LEFT JOIN CARI_KART as ck WITH(NOLOCK) ON ck.CARI_KART_ID = hru.HST_KURUM_ID AND ISNULL(ck.PSF_ID,0) = 0 
         WHERE (sks.SEVK_ETME_TRH >= ? AND sks.SEVK_ETME_TRH < DATEADD(day, 1, ?))
           AND sks.SEVK_DURUM IN (1,2,3,4,5,44)
           AND ISNULL(sks.PSF_ID,0) = 0
        ) AS ToplamHasta,
        
        (SELECT SUM(HST_BIRIM_FIYAT * HST_MIKTAR) 
         FROM SBS_HASTA_HAREKET WITH(NOLOCK) 
         WHERE ISLEM_TRH >= ? 
           AND ISLEM_TRH < DATEADD(day, 1, ?) 
           AND ISNULL(PSF_ID,0) = 0
        ) AS ToplamTutar
    """
    try:
        start_dt = datetime.strptime(f'{start_date_str} 00:00:00', '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(f'{end_date_str} 23:59:59', '%Y-%m-%d %H:%M:%S')
        df = pd.read_sql(sql, conn, params=[start_dt, end_dt, start_dt, end_dt])
        df['FATURA_NO'] = 'Canlı Veri'
        return df
    except Exception as e:
        print(f"SQL Hatası (Dinamik Dashboard): {e}")
        return pd.DataFrame()
    finally:
        conn.close()
