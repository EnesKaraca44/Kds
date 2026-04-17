import pandas as pd
from datetime import datetime
from .baglanti import baglanti_olustur
from .cache_helper import ttl_cache


@ttl_cache(maxsize=32, ttl=300)
def malzeme_tuketim_verisi_yukle(start_date_str, end_date_str):
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    sql_query = """
    SELECT
        BR.BIRIM_AD AS bransAdi,
        CAST(SH.SH_TARIH AS DATE) AS dusumTarih,
        SHH.HASTA_AD_SOYAD AS hastaAdSoyad,
        SHH.HEKIM_AD_SOYAD AS doktorAdSoyad,
        STOK.STOK_AD AS stokAd,
        SKH.HIZMET_SUT_TANIMI AS tetkikAdi,
        SUM(SH.SH_MIKTAR) AS dusumMiktar,
        SUM(SH.SH_TOPLAM) AS toplam
    FROM
        STOK_HAREKET (NOLOCK) AS SH
    INNER JOIN
        STOK_HAREKET_HASTA SHH ON SHH.STOK_FIS_ID = SH.SH_STOK_FIS_ID
        AND ISNULL(SHH.PSF_ID, 0) = 0
    INNER JOIN
        STOK_KART STOK ON SH.SH_STOKKART_ID = STOK.STOK_ID
        AND ISNULL(STOK.PSF_ID, 0) = 0
    LEFT JOIN
        SBS_DOKTOR (NOLOCK) DOKTOR ON SHH.HASTA_DOKTOR_ID = DOKTOR.KIMLIK_ID
        AND ISNULL(DOKTOR.PSF_ID, 0) = 0
    LEFT JOIN
        SBS_KLINIK (NOLOCK) KLINIK ON KLINIK.BIRIM_ID = DOKTOR.HEKIM_UST_SERVIS
        AND ISNULL(KLINIK.PSF_ID, 0) = 0
    LEFT JOIN
        BIRIM (NOLOCK) BR ON KLINIK.BIRIM_ID = BR.BIRIM_ID
        AND ISNULL(BR.PSF_ID, 0) = 0
    LEFT JOIN
        STOK_KART_HIZMET SKH (NOLOCK) ON SKH.STOK_ID = SH.SH_STOKKART_ID
        AND ISNULL(SKH.PSF_ID, 0) = 0
    WHERE
        ISNULL(SH.PSF_ID, 0) = 0
        AND SHH.HASTA_GELIS_TRH >= ?
        AND SHH.HASTA_GELIS_TRH < DATEADD(DAY, 1, ?)
    GROUP BY
        BR.BIRIM_AD,
        CAST(SH.SH_TARIH AS DATE),
        SHH.HASTA_AD_SOYAD,
        SHH.HEKIM_AD_SOYAD,
        STOK.STOK_AD,
        SKH.HIZMET_SUT_TANIMI
    ORDER BY 1, 2, 3, 5;
    """

    fallback_sql_query = """
    SELECT
        BR.BIRIM_AD AS bransAdi,
        CAST(SH.SH_TARIH AS DATE) AS dusumTarih,
        SHH.HASTA_AD_SOYAD AS hastaAdSoyad,
        SHH.HEKIM_AD_SOYAD AS doktorAdSoyad,
        STOK.STOK_AD AS stokAd,
        SKH.HIZMET_SUT_TANIMI AS tetkikAdi,
        SUM(SH.SH_MIKTAR) AS dusumMiktar,
        SUM(SH.SH_TOPLAM) AS toplam
    FROM
        STOK_HAREKET (NOLOCK) AS SH
    INNER JOIN
        STOK_HAREKET_HASTA SHH ON SHH.STOK_FIS_ID = SH.SH_STOK_FIS_ID
        AND ISNULL(SHH.PSF_ID, 0) = 0
    INNER JOIN
        STOK_KART STOK ON SH.SH_STOKKART_ID = STOK.STOK_ID
        AND ISNULL(STOK.PSF_ID, 0) = 0
    LEFT JOIN
        SBS_DOKTOR (NOLOCK) DOKTOR ON SHH.HASTA_DOKTOR_ID = DOKTOR.KIMLIK_ID
        AND ISNULL(DOKTOR.PSF_ID, 0) = 0
    LEFT JOIN
        SBS_KLINIK (NOLOCK) KLINIK ON KLINIK.BIRIM_ID = DOKTOR.HEKIM_UST_SERVIS
        AND ISNULL(KLINIK.PSF_ID, 0) = 0
    LEFT JOIN
        BIRIM (NOLOCK) BR ON KLINIK.BIRIM_ID = BR.BIRIM_ID
        AND ISNULL(BR.PSF_ID, 0) = 0
    LEFT JOIN
        STOK_KART_HIZMET SKH (NOLOCK) ON SKH.STOK_ID = SH.SH_STOKKART_ID
        AND ISNULL(SKH.PSF_ID, 0) = 0
    WHERE
        ISNULL(SH.PSF_ID, 0) = 0
        AND SH.SH_TARIH >= ?
        AND SH.SH_TARIH < DATEADD(DAY, 1, ?)
    GROUP BY
        BR.BIRIM_AD,
        CAST(SH.SH_TARIH AS DATE),
        SHH.HASTA_AD_SOYAD,
        SHH.HEKIM_AD_SOYAD,
        STOK.STOK_AD,
        SKH.HIZMET_SUT_TANIMI
    ORDER BY 1, 2, 3, 5;
    """

    try:
        start_dt = datetime.strptime(f'{start_date_str} 00:00:00', '%Y-%m-%d %H:%M:%S')
        end_dt_param = datetime.strptime(f'{end_date_str}', '%Y-%m-%d')

        try:
            df = pd.read_sql(sql_query, conn, params=[start_dt, end_dt_param])
        except Exception:
            # The first query filters by HASTA_GELIS_TRH. If that path fails on
            # some DB variants, fallback to SH_TARIH based filtering.
            df = pd.read_sql(fallback_sql_query, conn, params=[start_dt, end_dt_param])

        if not df.empty and 'dusumTarih' in df.columns:
            df['dusumTarih'] = pd.to_datetime(df['dusumTarih'])
        return df
    except Exception as e:
        print(f"Stock data loading error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


@ttl_cache(maxsize=8, ttl=3600)
def depo_birim_liste_yukle():
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    sql_query = """
    SELECT
        b.BIRIM_ID AS birimId,
        b.BIRIM_AD AS birimAd
    FROM BIRIM b WITH (NOLOCK)
    WHERE ISNULL(b.PSF_ID, 0) = 0
      AND b.BIRIM_OZELLIK = 514
    ORDER BY b.BIRIM_AD;
    """

    try:
        return pd.read_sql(sql_query, conn)
    except Exception as e:
        print(f"Depo birim liste yukleme hatasi: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


@ttl_cache(maxsize=32, ttl=300)
def depo_mevcut_verisi_yukle(start_date_str, end_date_str, birim_id=None, birim_id_list=None):
    """Depo mevcut stok ve miad verisi — Kategori 6 & 7 icin.
    birim_id: tek depo secimi
    birim_id_list: tum depolarin ID listesi (Tum Depolar icin)
    """
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    sql_query = """
    WITH SeviyeCTE AS (
        SELECT
            s.STOK_ID,
            s.SEVIYE_BIRIM_ID,
            s.SEVIYE_BIRIM_TUR_ID,
            s.STOK_SEVIYE_ASGARI,
            s.STOK_SEVIYE_AZAMI,
            s.STOK_SEVIYE_KRITIK
        FROM STOK_SEVIYE s WITH (NOLOCK)
        WHERE ISNULL(s.PSF_ID, 0) = 0
          AND s.SEVIYE_BIRIM_ID IN (SELECT * FROM dbo.TextToInConditionConvert(197, ','))
    ),
    FifoToplam AS (
        SELECT
            STOK_HAREKET_GIRIS_ID,
            SUM(ISNULL(STOK_HAREKET_MIKTAR, 0)) AS ToplamCikis
        FROM STOK_FIFO WITH (NOLOCK)
        WHERE ISNULL(PSF_ID, 0) = 0
        GROUP BY STOK_HAREKET_GIRIS_ID
    )
    SELECT
        shStokKod, shStokAd, shOlcuBirimAd, shMiktar,
        shMevcutMiktar, shCikisMiktar, shVadeTarih,
        birimAd, kritikStokMiktar, minStokMiktar, maxStokMiktar
    FROM (
        SELECT
            sk.STOK_KODU AS shStokKod,
            sk.STOK_AD AS shStokAd,
            td.TUR_DEGER AS shOlcuBirimAd,
            b.BIRIM_AD AS birimAd,
            sh.SH_VADE_TARIH AS shVadeTarih,
            CAST(sh.SH_MIKTAR * ISNULL(sh.SH_BIRIM_CARPAN, 1) AS DECIMAL(27,4)) AS shMiktar,
            ISNULL(f.ToplamCikis, 0) AS shCikisMiktar,
            CAST((sh.SH_MIKTAR * ISNULL(sh.SH_BIRIM_CARPAN, 1)) - ISNULL(f.ToplamCikis, 0) AS DECIMAL(27,4)) AS shMevcutMiktar,
            seviye.STOK_SEVIYE_ASGARI AS minStokMiktar,
            seviye.STOK_SEVIYE_AZAMI AS maxStokMiktar,
            seviye.STOK_SEVIYE_KRITIK AS kritikStokMiktar
        FROM STOK_HAREKET sh WITH (NOLOCK)
        INNER JOIN STOK_KART sk WITH (NOLOCK) ON sk.STOK_ID = sh.SH_STOKKART_ID
            AND (sk.STOK_OZELLIK & 1 = 1) AND ISNULL(sk.PSF_ID, 0) = 0
        INNER JOIN TUR_DETAY td WITH (NOLOCK) ON td.TUR_DETAY_ID = sh.SH_BIRIM_TUR_ID
            AND ISNULL(td.PSF_ID, 0) = 0
        INNER JOIN STOK_HAREKET_TUR sht WITH (NOLOCK) ON sh.SH_HAREKET_TUR_ID = sht.STOK_HAREKET_TUR_ID
            AND ISNULL(sht.PSF_ID, 0) = 0
        INNER JOIN BIRIM b WITH (NOLOCK) ON b.BIRIM_ID = sh.SH_BIRIM_ID
            AND ISNULL(b.PSF_ID, 0) = 0
        LEFT JOIN FifoToplam f ON f.STOK_HAREKET_GIRIS_ID = sh.STOK_HAREKET_ID
        LEFT JOIN SeviyeCTE seviye ON sh.SH_STOKKART_ID = seviye.STOK_ID
            AND sh.SH_BIRIM_TUR_ID = seviye.SEVIYE_BIRIM_TUR_ID
            AND sh.SH_BIRIM_ID = seviye.SEVIYE_BIRIM_ID
        WHERE ISNULL(sh.PSF_ID, 0) = 0
          AND sh.SH_TARIH BETWEEN ? AND ?
          AND sht.HAREKET_ENVANTER_TIP = 1
          AND sht.HAREKET_FIS_TIP <> 2
    ) AS FinalTablo
    WHERE shMevcutMiktar > 0
    ORDER BY shStokAd ASC;
    """

    try:
        start_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date_str, '%Y-%m-%d')
        params = [start_dt, end_dt]

        active_ids = []
        if birim_id:
            active_ids = [int(birim_id)]
        elif birim_id_list:
            active_ids = [int(x) for x in birim_id_list]

        if active_ids:
            placeholders = ','.join(['?'] * len(active_ids))
            sql_query = sql_query.replace(
                "FifoToplam AS (",
                "SeciliBirimler AS (\n"
                "        SELECT b.BIRIM_ID\n"
                "        FROM BIRIM b WITH (NOLOCK)\n"
                "        WHERE ISNULL(b.PSF_ID, 0) = 0\n"
                f"          AND b.BIRIM_ID IN ({placeholders})\n"
                "        UNION ALL\n"
                "        SELECT c.BIRIM_ID\n"
                "        FROM BIRIM c WITH (NOLOCK)\n"
                "        INNER JOIN SeciliBirimler sb ON c.UST_BIRIM_ID = sb.BIRIM_ID\n"
                "        WHERE ISNULL(c.PSF_ID, 0) = 0\n"
                "    ),\n"
                "    FifoToplam AS ("
            )
            sql_query = sql_query.replace(
                "AND sht.HAREKET_FIS_TIP <> 2",
                "AND sht.HAREKET_FIS_TIP <> 2\n"
                "          AND sh.SH_BIRIM_ID IN (SELECT BIRIM_ID FROM SeciliBirimler)"
            )
            params = active_ids + params

        df = pd.read_sql(sql_query, conn, params=params)

        if not df.empty and 'shVadeTarih' in df.columns:
            df['shVadeTarih'] = pd.to_datetime(df['shVadeTarih'], errors='coerce')

        for col in ('shMiktar', 'shMevcutMiktar', 'shCikisMiktar',
                     'kritikStokMiktar', 'minStokMiktar', 'maxStokMiktar'):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        return df
    except Exception as e:
        print(f"Depo mevcut veri yukleme hatasi: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
