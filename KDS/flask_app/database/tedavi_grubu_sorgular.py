import pandas as pd
from datetime import datetime
from .baglanti import baglanti_olustur


def tedavi_grubu_verisi_yukle(start_date_str, end_date_str):
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    sql_query = """
         SELECT
    ISNULL(skhg.GURUP_TANIMI, 'Belirtilmemiş') AS TEDAVI_GRUBU_ADI,
    hasta.HASTA_KODU                          AS HASTA_KODU,
    k.KIMLIK_AD + ' ' + k.KIMLIK_SOYAD        AS HASTA_ADI_SOYADI,
    hru.HST_GELIS_TRH                         AS HASTA_GELIS_TARIHI,
    hru.HST_GELIS_ID                          AS HASTA_GELIS_NO,
    ck.CARI_KART_ADI                          AS HASTA_KURUM_ADI,
    skh.HIZMET_SUT_KODU                       AS TETKIK_BUTCE_KODU,
    skh.HIZMET_SUT_TANIMI                     AS TETKIK_ADI,
    shh.ISLEM_TRH                             AS TETKIK_TARIHI,
    b.BIRIM_AD                                AS TETKIK_KLINIK_ADI,
    shh.HST_BIRIM_FIYAT                       AS TETKIK_BIRIM_UCRET,
    -- İŞLEM ADETİ
    SUM(ISNULL(shh.HST_MIKTAR, shh.HST_ADET)) AS TOPLAM_ADET,
    -- D_ORAN/K_ORAN çarpanını tüm hesaplamalara uyguluyoruz (Kullanıcının ilettiği mantık)
    -- TOPLAM ÜCRET
    SUM(CAST(
        (ISNULL(shh.HST_MIKTAR,1) * ISNULL(shh.HST_BIRIM_FIYAT,0)) * 
        CASE 
            WHEN ISNULL(NULLIF(shh.KONSULTAN_HEKIM_KIMLIK_ID, shh.HEKIM_KIMLIK_ID), 0) > 0 THEN sdo.K_ORAN 
            ELSE sdo.D_ORAN 
        END
    AS FLOAT)) AS TETKIK_TOPLAM_UCRET,
    -- MESAI İÇİ / DIŞI PUANLAR
    SUM(
        CASE 
            WHEN td.TUR_DEGER_KOD = 'MESAIICI' AND ISNULL(shh.HIZMET_PUAN_ALMASIN,0) = 0 THEN 
                (shh.HIZMET_PUAN1 * ISNULL(shh.HIZMET_PUAN1_CARPAN,1)) * CASE WHEN ISNULL(NULLIF(shh.KONSULTAN_HEKIM_KIMLIK_ID, shh.HEKIM_KIMLIK_ID), 0) > 0 THEN sdo.K_ORAN ELSE sdo.D_ORAN END
            WHEN td.TUR_DEGER_KOD = 'ISLEMSAATINEGORE' AND ISNULL(shh.HIZMET_PUAN_ALMASIN,0) = 0 AND shh.ISLEM_SAAT > 0 AND shh.ISLEM_SAAT < sk.MESAI_DISI_SAAT1 THEN 
                (shh.HIZMET_PUAN1 * ISNULL(shh.HIZMET_PUAN1_CARPAN,1)) * CASE WHEN ISNULL(NULLIF(shh.KONSULTAN_HEKIM_KIMLIK_ID, shh.HEKIM_KIMLIK_ID), 0) > 0 THEN sdo.K_ORAN ELSE sdo.D_ORAN END
            ELSE 0
        END
    ) AS MESAI_ICI_PUAN,
    SUM(
        CASE 
            WHEN td.TUR_DEGER_KOD = 'MESAIDISI' AND ISNULL(shh.HIZMET_PUAN_ALMASIN,0) = 0 THEN 
                (shh.HIZMET_PUAN1 * ISNULL(shh.HIZMET_PUAN1_CARPAN,1)) * CASE WHEN ISNULL(NULLIF(shh.KONSULTAN_HEKIM_KIMLIK_ID, shh.HEKIM_KIMLIK_ID), 0) > 0 THEN sdo.K_ORAN ELSE sdo.D_ORAN END
            WHEN td.TUR_DEGER_KOD = 'ISLEMSAATINEGORE' AND ISNULL(shh.HIZMET_PUAN_ALMASIN,0) = 0 AND shh.ISLEM_SAAT >= sk.MESAI_DISI_SAAT1 AND shh.ISLEM_SAAT <= sk.MESAI_DISI_SAAT2 THEN 
                (shh.HIZMET_PUAN1 * ISNULL(shh.HIZMET_PUAN1_CARPAN,1)) * CASE WHEN ISNULL(NULLIF(shh.KONSULTAN_HEKIM_KIMLIK_ID, shh.HEKIM_KIMLIK_ID), 0) > 0 THEN sdo.K_ORAN ELSE sdo.D_ORAN END
            ELSE 0
        END
    ) AS MESAI_DISI_PUAN,
    -- SAYFA İÇİN TOPLAM PUAN
    SUM(
        CASE 
            WHEN ISNULL(shh.HIZMET_PUAN_ALMASIN,0) = 0 THEN
                (shh.HIZMET_PUAN1 * ISNULL(shh.HIZMET_PUAN1_CARPAN,1)) * CASE WHEN ISNULL(NULLIF(shh.KONSULTAN_HEKIM_KIMLIK_ID, shh.HEKIM_KIMLIK_ID), 0) > 0 THEN sdo.K_ORAN ELSE sdo.D_ORAN END
            ELSE 0
        END
    ) AS TETKIK_TOPLAM_PUAN,
    -- DETAY İÇİN GRUP TOPLAM ADET (opsiyonel, python kullanmıyor ama eski yapıya benzer)
    COUNT(DISTINCT CAST(hasta.HASTA_KODU AS NVARCHAR) + CAST(hru.HST_GELIS_ID AS NVARCHAR)) AS GRUP_TOPLAM_ADET,
    -- HESAPLANAN_PUAN: istersen burada kendi formülünü kullanabilirsin
    SUM(
        CASE 
            WHEN ISNULL(shh.HIZMET_PUAN_ALMASIN,0) = 0 THEN
                (shh.HIZMET_PUAN1 * ISNULL(shh.HIZMET_PUAN1_CARPAN,1)) * CASE WHEN ISNULL(NULLIF(shh.KONSULTAN_HEKIM_KIMLIK_ID, shh.HEKIM_KIMLIK_ID), 0) > 0 THEN sdo.K_ORAN ELSE sdo.D_ORAN END
            ELSE 0
        END
    ) AS HESAPLANAN_PUAN
FROM SBS_HASTA_HAREKET AS shh WITH (NOLOCK)
INNER JOIN SBS_HASTA_RESMI_UCRETLI AS hru WITH (NOLOCK)
    ON hru.HST_GELIS_ID = shh.HST_GELIS_ID
   AND ISNULL(hru.PSF_ID,0) = 0
INNER JOIN STOK_KART_HIZMET AS skh WITH (NOLOCK)
    ON skh.STOK_ID = shh.STOK_ID
   AND ISNULL(skh.PSF_ID,0) = 0
LEFT JOIN STOK_KART_HIZMET_GRUP AS skhg WITH (NOLOCK)
    ON skhg.GURUP_ID = skh.GURUP_ID
   AND ISNULL(skhg.PSF_ID,0) = 0
LEFT JOIN SBS_DOKTOR AS sd WITH (NOLOCK)
    ON sd.KIMLIK_ID = shh.HEKIM_KIMLIK_ID
   AND ISNULL(sd.PSF_ID,0) = 0
INNER JOIN KIMLIK AS k WITH (NOLOCK)
    ON k.KIMLIK_ID = shh.HASTA_KIMLIK_ID
INNER JOIN SBS_HASTA AS hasta WITH (NOLOCK)
    ON hasta.HASTA_KIMLIK_ID = k.KIMLIK_ID
   AND ISNULL(hasta.PSF_ID,0) = 0
LEFT JOIN BIRIM AS b WITH (NOLOCK)
    ON b.BIRIM_ID = shh.KLINIK_BIRIM_ID
   AND ISNULL(b.PSF_ID,0) = 0
LEFT JOIN SBS_KLINIK AS sk WITH (NOLOCK)
    ON sk.BIRIM_ID = shh.KLINIK_BIRIM_ID
   AND ISNULL(sk.PSF_ID,0) = 0
LEFT JOIN CARI_KART AS ck WITH (NOLOCK)
    ON ck.CARI_KART_ID = hru.HST_KURUM_ID
   AND ISNULL(ck.PSF_ID,0) = 0
LEFT JOIN BRANS AS brs WITH (NOLOCK)
    ON brs.BRANS_ID = sk.BRANS_ID
   AND ISNULL(brs.PSF_ID,0) = 0
LEFT JOIN TUR_DETAY AS td WITH (NOLOCK)
    ON td.TUR_DETAY_ID = sk.MESAI_DURUMU
   AND ISNULL(td.PSF_ID,0) = 0
INNER JOIN SBS_DOKTOR_ORAN AS sdo WITH (NOLOCK) 
    ON sdo.K = SIGN(ISNULL(NULLIF(shh.KONSULTAN_HEKIM_KIMLIK_ID, shh.HEKIM_KIMLIK_ID), 0)) 
   AND sdo.D = SIGN(ISNULL(shh.HEKIM_KIMLIK_ID, 0)) 
   AND sdo.C = SIGN(ISNULL(shh.OGRENCI_HEKIM_KIMLIK_ID, 0)) 
   AND sdo.TASLAK_ID = 1 
   AND ISNULL(sdo.PSF_ID, 0) = 0
WHERE
    ISNULL(shh.PSF_ID,0) = 0
    AND ISNULL(EK_ODEME_YANSIMASIN,0) <= 0
    AND shh.ISLEM_TRH BETWEEN ? AND ?
GROUP BY
    ISNULL(skhg.GURUP_TANIMI, 'Belirtilmemiş'),
    hasta.HASTA_KODU,
    k.KIMLIK_AD + ' ' + k.KIMLIK_SOYAD,
    hru.HST_GELIS_TRH,
    hru.HST_GELIS_ID,
    ck.CARI_KART_ADI,
    skh.HIZMET_SUT_KODU,
    skh.HIZMET_SUT_TANIMI,
    shh.ISLEM_TRH,
    b.BIRIM_AD,
    shh.HST_BIRIM_FIYAT;
    """

    try:
        start_dt = datetime.strptime(f'{start_date_str} 00:00:00', '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(f'{end_date_str} 23:59:59', '%Y-%m-%d %H:%M:%S')

        df = pd.read_sql(sql_query, conn, params=[start_dt, end_dt])
        df['HASTA_GELIS_TARIHI'] = pd.to_datetime(df['HASTA_GELIS_TARIHI'])
        df['TETKIK_TARIHI'] = pd.to_datetime(df['TETKIK_TARIHI'])
        return df
    except Exception as e:
        print(f"❌ Tedavi grubu verisi yüklenirken hata: {e}")
        return pd.DataFrame()
    finally:
        conn.close()




