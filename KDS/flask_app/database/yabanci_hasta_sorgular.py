import pandas as pd
from datetime import datetime
from .baglanti import baglanti_olustur


def yabanci_hasta_verisi_yukle(start_date_str, end_date_str):
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    sql_query = """
        SELECT
            k.KIMLIK_TC_NO AS HstNufus,
            (k.KIMLIK_AD + ' ' + k.KIMLIK_SOYAD) AS HastaAdi,
            SUM(
                CAST(
                    ISNULL(shh.HST_BIRIM_FIYAT, 0) * ISNULL(shh.HST_MIKTAR, ISNULL(shh.HST_ADET, 1))
                    AS FLOAT
                )
            ) AS Fiyat,
            CAST(sevk.SEVK_ETME_TRH AS DATETIME) AS hstgtrh,
            CAST(hru.HST_GELIS_ID AS INT) AS hstsra,
            CAST(NULL AS NVARCHAR(10)) AS HstUyruk,
            u.ULKE_AD AS Ulke,
            CAST(NULL AS NVARCHAR(50)) AS GSS_TAKIP_NO,
            CAST(skh.HIZMET_SUT_KODU AS NVARCHAR(50)) AS hsttetno,
            CASE
                WHEN k.CINSIYET_TUR_ID = 1 THEN 'Erkek'
                WHEN k.CINSIYET_TUR_ID = 2 THEN 'Bayan'
                ELSE 'Bilinmiyor'
            END AS Cinsiyet,
            CAST(k.KIMLIK_DOGUM_TRH AS DATETIME) AS HstDtrh
        FROM SBS_HASTA_HAREKET AS shh WITH (NOLOCK)
        INNER JOIN SBS_HASTA_RESMI_UCRETLI AS hru WITH (NOLOCK)
            ON hru.HST_GELIS_ID = shh.HST_GELIS_ID
            AND ISNULL(hru.PSF_ID, 0) = 0
        LEFT JOIN SBS_KLINIK_SEVK AS sevk WITH (NOLOCK)
            ON sevk.SEVK_HST_GELIS_ID = hru.HST_GELIS_ID
            AND ISNULL(sevk.PSF_ID, 0) = 0
        INNER JOIN STOK_KART_HIZMET AS skh WITH (NOLOCK)
            ON skh.STOK_ID = shh.STOK_ID
            AND ISNULL(skh.PSF_ID, 0) = 0
        INNER JOIN KIMLIK AS k WITH (NOLOCK)
            ON k.KIMLIK_ID = shh.HASTA_KIMLIK_ID
        INNER JOIN SBS_HASTA AS sh WITH (NOLOCK)
            ON sh.HASTA_KIMLIK_ID = k.KIMLIK_ID
            AND ISNULL(sh.PSF_ID, 0) = 0
        LEFT JOIN ULKE AS u WITH (NOLOCK)
            ON u.ULKE_ID = sh.HASTA_ULKE
            AND ISNULL(u.PSF_ID, 0) = 0
        WHERE 1 = 1
            AND ISNULL(shh.PSF_ID, 0) = 0
            AND ISNULL(sevk.SEVK_DURUM, 0) IN (1, 2, 3, 4, 5, 44)
            AND ISNULL(u.ULKE_AD, '') <> ''
            AND ISNULL(u.ULKE_AD, '') NOT LIKE '%Türkiye%'
            AND (sevk.SEVK_ETME_TRH >= ?)
            AND (sevk.SEVK_ETME_TRH < DATEADD(day, 1, ?))
        GROUP BY
            k.KIMLIK_TC_NO,
            (k.KIMLIK_AD + ' ' + k.KIMLIK_SOYAD),
            CAST(sevk.SEVK_ETME_TRH AS DATETIME),
            CAST(hru.HST_GELIS_ID AS INT),
            u.ULKE_AD,
            CAST(skh.HIZMET_SUT_KODU AS NVARCHAR(50)),
            k.CINSIYET_TUR_ID,
            CAST(k.KIMLIK_DOGUM_TRH AS DATETIME)
        HAVING
            SUM(
                CAST(
                    ISNULL(shh.HST_BIRIM_FIYAT, 0) * ISNULL(shh.HST_MIKTAR, ISNULL(shh.HST_ADET, 1))
                    AS FLOAT
                )
            ) > 0
        ORDER BY (k.KIMLIK_AD + ' ' + k.KIMLIK_SOYAD);
    """

    try:
        start_dt = datetime.strptime(f'{start_date_str} 00:00:00', '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(f'{end_date_str} 23:59:59', '%Y-%m-%d %H:%M:%S')

        df = pd.read_sql(sql_query, conn, params=[start_dt, end_dt])

        if not df.empty:
            df['hstgtrh'] = pd.to_datetime(df['hstgtrh'], errors='coerce')
            df['HstDtrh'] = pd.to_datetime(df['HstDtrh'], errors='coerce')

            current_year = datetime.now().year
            df['YAS'] = (current_year - df['HstDtrh'].dt.year).astype('Int64')
            df = df.drop(columns=['HstDtrh'])

        return df
    except Exception as e:
        print(f"❌ Yabancı hasta verisi hatası: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
