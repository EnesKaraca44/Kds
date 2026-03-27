import pandas as pd
from datetime import datetime

from .baglanti import baglanti_olustur


def kasa_ozet_verisi_yukle(start_date_str: str, end_date_str: str) -> pd.DataFrame:
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    sql_query = """
        SELECT
            k.KASA_ID AS kasaId,
            k.KASA_AD AS kasaAd,
            SUM(
                CASE
                    WHEN sht.HAREKET_ENVANTER_TIP = 1 AND ISNULL(kh.KH_IPTAL, 0) = 0 THEN
                        CASE
                            WHEN ISNULL(kh.KH_ODENEN_TUTAR, 0) > 0 THEN ISNULL(kh.KH_ODENEN_TUTAR, 0)
                            ELSE kh.KH_NET_TUTAR
                        END
                    ELSE 0
                END
            ) AS tahsilatToplam,
            SUM(
                CASE
                    WHEN sht.HAREKET_ENVANTER_TIP = 2 AND ISNULL(kh.KH_IPTAL, 0) = 0 THEN kh.KH_Tutar
                    ELSE 0
                END
            ) AS odemeToplam,
            SUM(CASE WHEN ISNULL(kh.KH_IPTAL, 0) <> 0 THEN kh.KH_Tutar ELSE 0 END) AS iptalToplam,
            ABS(
                SUM(
                    CASE
                        WHEN sht.HAREKET_ENVANTER_TIP = 1 AND ISNULL(kh.KH_IPTAL, 0) = 0 THEN
                            CASE
                                WHEN ISNULL(kh.KH_ODENEN_TUTAR, 0) > 0 THEN ISNULL(kh.KH_ODENEN_TUTAR, 0)
                                ELSE kh.KH_NET_TUTAR
                            END
                        ELSE 0
                    END
                )
                - SUM(
                    CASE
                        WHEN sht.HAREKET_ENVANTER_TIP = 2 AND ISNULL(kh.KH_IPTAL, 0) = 0 THEN kh.KH_Tutar
                        ELSE 0
                    END
                )
            ) AS kalan
        FROM KASA_HAREKET AS kh WITH (NOLOCK)
        INNER JOIN KASA AS k WITH (NOLOCK)
            ON k.KASA_ID = kh.KH_KASA_ID
           AND ISNULL(k.PSF_ID, 0) = 0
        INNER JOIN STOK_HAREKET_TUR AS sht WITH (NOLOCK)
            ON sht.STOK_HAREKET_TUR_ID = kh.KH_HAREKET_TUR_ID
           AND ISNULL(sht.PSF_ID, 0) = 0
        INNER JOIN BIRIM AS b WITH (NOLOCK)
            ON k.KASA_BIRIM_ID = b.BIRIM_ID
           AND ISNULL(b.PSF_ID, 0) = 0
        WHERE
            ISNULL(kh.PSF_ID, 0) = 0
            AND kh.KH_TRH >= ?
            AND kh.KH_TRH < DATEADD(day, 1, ?)
        GROUP BY
            k.KASA_ID,
            k.KASA_AD
        ORDER BY
            k.KASA_AD;
    """

    try:
        start_dt = datetime.strptime(f"{start_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(f"{end_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
        return pd.read_sql(sql_query, conn, params=[start_dt, end_dt])
    except Exception as e:
        print(f"❌ Vezne kasa özet verisi yüklenirken hata: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def kasa_hareket_turu_verisi_yukle(start_date_str: str, end_date_str: str, kasa_id: int) -> pd.DataFrame:
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    sql_query = """
        SELECT
            k.KASA_ID AS kasaId,
            k.KASA_AD AS kasaAd,
            sht.HAREKET_TUR_AD AS hareketTurAd,
            SUM(
                CASE
                    WHEN sht.HAREKET_ENVANTER_TIP = 1 AND ISNULL(kh.KH_IPTAL, 0) = 0 THEN
                        CASE
                            WHEN ISNULL(kh.KH_ODENEN_TUTAR, 0) > 0 THEN ISNULL(kh.KH_ODENEN_TUTAR, 0)
                            ELSE kh.KH_NET_TUTAR
                        END
                    ELSE 0
                END
            ) AS tahsilatToplam,
            SUM(
                CASE
                    WHEN sht.HAREKET_ENVANTER_TIP = 2 AND ISNULL(kh.KH_IPTAL, 0) = 0 THEN kh.KH_Tutar
                    ELSE 0
                END
            ) AS odemeToplam
        FROM KASA_HAREKET AS kh WITH (NOLOCK)
        INNER JOIN KASA AS k WITH (NOLOCK)
            ON k.KASA_ID = kh.KH_KASA_ID
           AND ISNULL(k.PSF_ID, 0) = 0
        INNER JOIN STOK_HAREKET_TUR AS sht WITH (NOLOCK)
            ON sht.STOK_HAREKET_TUR_ID = kh.KH_HAREKET_TUR_ID
           AND ISNULL(sht.PSF_ID, 0) = 0
        LEFT JOIN KIMLIK AS kml WITH (NOLOCK)
            ON kh.KH_KIMLIK_ID = kml.KIMLIK_ID
           AND ISNULL(kml.PSF_ID, 0) = 0
        WHERE
            ISNULL(kh.PSF_ID, 0) = 0
            AND kh.KH_KASA_ID = ?
            AND kh.KH_TRH >= ?
            AND kh.KH_TRH < DATEADD(day, 1, ?)
        GROUP BY
            k.KASA_ID,
            k.KASA_AD,
            sht.HAREKET_TUR_AD
        ORDER BY
            sht.HAREKET_TUR_AD;
    """

    try:
        start_dt = datetime.strptime(f"{start_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(f"{end_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
        return pd.read_sql(sql_query, conn, params=[int(kasa_id), start_dt, end_dt])
    except Exception as e:
        print(f"❌ Vezne hareket türü verisi yüklenirken hata: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def kasa_aylik_verisi_yukle(start_date_str: str, end_date_str: str, kasa_id: int) -> pd.DataFrame:
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    sql_query = """
        SELECT
            ISNULL(StokMaliyet.Yil, YEAR(?)) AS Yil,
            tdm.TUR_DETAY_SIRA AS Ay,
            tdm.TUR_DEGER_KOD AS AyAdi,
            StokMaliyet.TahsilatToplam,
            StokMaliyet.OdemeToplam
        FROM TUR_DETAY AS tdm WITH (NOLOCK)
        LEFT OUTER JOIN (
            SELECT
                k.KASA_ID AS KasaID,
                k.KASA_AD AS KasaAd,
                DATEPART(YEAR, kh.KH_TRH) AS Yil,
                DATEPART(MONTH, kh.KH_TRH) AS Ay,
                SUM(
                    CASE
                        WHEN sht.HAREKET_ENVANTER_TIP = 1 AND ISNULL(kh.KH_IPTAL, 0) = 0 THEN
                            CASE
                                WHEN ISNULL(kh.KH_ODENEN_TUTAR, 0) > 0 THEN ISNULL(kh.KH_ODENEN_TUTAR, 0)
                                ELSE kh.KH_NET_TUTAR
                            END
                        ELSE 0
                    END
                ) AS TahsilatToplam,
                SUM(
                    CASE
                        WHEN sht.HAREKET_ENVANTER_TIP = 2 AND ISNULL(kh.KH_IPTAL, 0) = 0 THEN kh.KH_Tutar
                        ELSE 0
                    END
                ) AS OdemeToplam
            FROM KASA_HAREKET AS kh WITH (NOLOCK)
            INNER JOIN KASA AS k WITH (NOLOCK)
                ON k.KASA_ID = kh.KH_KASA_ID
               AND ISNULL(k.PSF_ID, 0) = 0
            INNER JOIN STOK_HAREKET_TUR AS sht WITH (NOLOCK)
                ON sht.STOK_HAREKET_TUR_ID = kh.KH_HAREKET_TUR_ID
               AND ISNULL(sht.PSF_ID, 0) = 0
            WHERE
                ISNULL(kh.PSF_ID, 0) = 0
                AND kh.KH_KASA_ID = ?
                AND kh.KH_TRH >= ?
                AND kh.KH_TRH < DATEADD(day, 1, ?)
            GROUP BY
                k.KASA_ID,
                k.KASA_AD,
                DATEPART(YEAR, kh.KH_TRH),
                DATEPART(MONTH, kh.KH_TRH)
        ) AS StokMaliyet
            ON tdm.TUR_DETAY_SIRA = StokMaliyet.Ay
        WHERE
            tdm.TUR_ID = 10037
        ORDER BY
            tdm.TUR_DETAY_SIRA;
    """

    try:
        start_dt = datetime.strptime(f"{start_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(f"{end_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
        return pd.read_sql(sql_query, conn, params=[start_dt, int(kasa_id), start_dt, end_dt])
    except Exception as e:
        print(f"❌ Vezne aylık verisi yüklenirken hata: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

