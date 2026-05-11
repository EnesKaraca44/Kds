import pandas as pd
from datetime import datetime
from .baglanti import baglanti_olustur
from .cache_helper import ttl_cache
from .sql_api_client import get_remote_sql

_LOCAL_FALLBACK_SQL = """
    SELECT
        ISNULL(sh.HASTA_KODU, hstk.HASTAM_AKTARIM_HstKod)   AS HstKod,
        br.BIRIM_AD                                         AS SrvAd,
        ISNULL(sd.DOKTOR_AD + ' ' + sd.DOKTOR_SOYAD, 'BELİRTİLMEMİŞ') AS DOKTOR_ADI,
        ck.CARI_KART_ADI                                    AS KrmAdi,
        sevk.SEVK_KABUL_ETME_TRH                            AS KAYIT_TARIHI,
        CONVERT(varchar(5), sevk.SEVK_KABUL_ETME_TRH, 108)  AS Saat,
        hru.HST_GELIS_TRH                                   AS HstGelisTrh
    FROM SBS_KLINIK_SEVK AS sevk WITH (NOLOCK)
    LEFT JOIN SBS_HASTA_RESMI_UCRETLI AS hru WITH (NOLOCK)
           ON hru.HST_GELIS_ID = sevk.SEVK_HST_GELIS_ID
          AND ISNULL(hru.PSF_ID, 0) = 0
    INNER JOIN BIRIM AS br WITH (NOLOCK)
            ON br.BIRIM_ID = sevk.SEVK_EDILEN_KLINIK_BIRIM_ID
           AND ISNULL(br.PSF_ID, 0) = 0
    LEFT JOIN SBS_DOKTOR AS sd WITH (NOLOCK)
           ON sd.KIMLIK_ID = sevk.SEVK_EDILEN_HEKIM_KIMLIK_ID
          AND ISNULL(sd.PSF_ID, 0) = 0
    INNER JOIN KIMLIK AS hstk WITH (NOLOCK)
            ON hstk.KIMLIK_ID = hru.HASTA_KIMLIK_ID
           AND ISNULL(hstk.PSF_ID, 0) = 0
    INNER JOIN SBS_HASTA AS sh WITH (NOLOCK)
            ON sh.HASTA_KIMLIK_ID = hstk.KIMLIK_ID
           AND ISNULL(sh.PSF_ID, 0) = 0
    LEFT JOIN CARI_KART AS ck WITH (NOLOCK)
           ON ck.CARI_KART_ID = hru.HST_KURUM_ID
          AND ISNULL(ck.PSF_ID, 0) = 0
    WHERE 1 = 1
      AND sevk.SEVK_DURUM IN (1,2,3,4,5,44)
      AND sevk.SEVK_KABUL_ETME_TRH >= ?
      AND sevk.SEVK_KABUL_ETME_TRH < DATEADD(day, 1, ?)
"""


@ttl_cache(maxsize=32, ttl=600)
def poliklinik_performans_verisi_yukle(start_date_str, end_date_str):
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    try:
        sql_query = get_remote_sql(
            "poliklinik.poliklinik_performans_verisi_yukle",
            {"start_date": start_date_str, "end_date": end_date_str},
        )
        if not sql_query:
            # API tarafinda kod tanimi yoksa sayfa bosa dusmesin.
            sql_query = _LOCAL_FALLBACK_SQL

        if "?" in sql_query:
            start_dt = datetime.strptime(f"{start_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(f"{end_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
            df = pd.read_sql(sql_query, conn, params=[start_dt, end_dt])
        else:
            df = pd.read_sql(sql_query, conn)
        if 'KAYIT_TARIHI' in df.columns:
            df['KAYIT_TARIHI'] = pd.to_datetime(df['KAYIT_TARIHI'])
        if 'HstGelisTrh' in df.columns:
            df['HstGelisTrh'] = pd.to_datetime(df['HstGelisTrh'])
        return df
    except Exception as e:
        print(f"Poliklinik verisi yuklenirken hata: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
