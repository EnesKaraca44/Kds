import pandas as pd
from datetime import datetime
from .connection import get_db_connection


def load_stock_consumption_data(start_date_str, end_date_str):
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()

    sql_query = """
    SELECT
        klinik.GSS_KLINIK_ADI AS bransAdi,
        CAST(hareket.SH_TARIH AS DATE) AS dusumTarih,
        hasta.HASTA_AD_SOYAD AS hastaAdSoyad,
        hasta.HEKIM_AD_SOYAD AS doktorAdSoyad,
        stok.STOK_AD AS stokAd,
        t.tAd AS tetkikAdi,
        SUM(hareket.SH_MIKTAR) AS dusumMiktar,
        SUM(hareket.SH_TOPLAM) AS toplam
    FROM
        DEAL..STOK_HAREKET_HASTA hasta
    INNER JOIN
        DEAL..STOK_HAREKET hareket ON hasta.STOK_FIS_ID = hareket.SH_STOK_FIS_ID
        AND ISNULL(hareket.PSF_ID, 0) = 0
    INNER JOIN
        DEAL..STOK_KART stok ON hareket.SH_STOKKART_ID = stok.STOK_ID
        AND ISNULL(stok.PSF_ID, 0) = 0
    LEFT JOIN
        TblDoktor (NOLOCK) doktor ON hasta.HASTA_DOKTOR_ID = doktor.DktNo
    LEFT JOIN
        TblGSS_KLINIK (NOLOCK) klinik ON klinik.GSS_KLINIK_KODU = doktor.dkno
    LEFT JOIN
        Tbltetkikad t (NOLOCK) ON LTRIM(RTRIM(UPPER(t.tKodu))) = LTRIM(RTRIM(UPPER(hasta.HBYS_ILAC_SARF_TETKIK_KODU)))
    WHERE
        ISNULL(hasta.PSF_ID, 0) = 0
        AND hasta.HASTA_GELIS_TRH >= ?
        AND hasta.HASTA_GELIS_TRH < DATEADD(DAY, 1, ?)
    GROUP BY
        klinik.GSS_KLINIK_ADI,
        CAST(hareket.SH_TARIH AS DATE),
        hasta.HASTA_AD_SOYAD,
        hasta.HEKIM_AD_SOYAD,
        stok.STOK_AD,
        t.tAd
    ORDER BY 1, 2, 3, 5;
    """

    fallback_sql_query = """
    SELECT
        klinik.GSS_KLINIK_ADI AS bransAdi,
        CAST(hareket.SH_TARIH AS DATE) AS dusumTarih,
        hasta.HASTA_AD_SOYAD AS hastaAdSoyad,
        hasta.HEKIM_AD_SOYAD AS doktorAdSoyad,
        stok.STOK_AD AS stokAd,
        CAST(NULL AS NVARCHAR(250)) AS tetkikAdi,
        SUM(hareket.SH_MIKTAR) AS dusumMiktar,
        SUM(hareket.SH_TOPLAM) AS toplam
    FROM
        DEAL..STOK_HAREKET_HASTA hasta
    INNER JOIN
        DEAL..STOK_HAREKET hareket ON hasta.STOK_FIS_ID = hareket.SH_STOK_FIS_ID
        AND ISNULL(hareket.PSF_ID, 0) = 0
    INNER JOIN
        DEAL..STOK_KART stok ON hareket.SH_STOKKART_ID = stok.STOK_ID
        AND ISNULL(stok.PSF_ID, 0) = 0
    LEFT JOIN
        TblDoktor (NOLOCK) doktor ON hasta.HASTA_DOKTOR_ID = doktor.DktNo
    LEFT JOIN
        TblGSS_KLINIK (NOLOCK) klinik ON klinik.GSS_KLINIK_KODU = doktor.dkno
    WHERE
        ISNULL(hasta.PSF_ID, 0) = 0
        AND hasta.HASTA_GELIS_TRH >= ?
        AND hasta.HASTA_GELIS_TRH < DATEADD(DAY, 1, ?)
    GROUP BY
        klinik.GSS_KLINIK_ADI,
        CAST(hareket.SH_TARIH AS DATE),
        hasta.HASTA_AD_SOYAD,
        hasta.HEKIM_AD_SOYAD,
        stok.STOK_AD
    ORDER BY 1, 2, 3, 5;
    """

    try:
        start_dt = datetime.strptime(f'{start_date_str} 00:00:00', '%Y-%m-%d %H:%M:%S')
        end_dt_param = datetime.strptime(f'{end_date_str}', '%Y-%m-%d')

        try:
            df = pd.read_sql(sql_query, conn, params=[start_dt, end_dt_param])
        except Exception as query_error:
            # Some DB versions do not have HBYS_ILAC_SARF_TETKIK_KODU.
            # In that case, fallback query keeps analysis running without tetkik detail.
            if "HBYS_ILAC_SARF_TETKIK_KODU" in str(query_error).upper():
                df = pd.read_sql(fallback_sql_query, conn, params=[start_dt, end_dt_param])
            else:
                raise

        if not df.empty and 'dusumTarih' in df.columns:
            df['dusumTarih'] = pd.to_datetime(df['dusumTarih'])
        return df
    except Exception as e:
        print(f"Stock data loading error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
