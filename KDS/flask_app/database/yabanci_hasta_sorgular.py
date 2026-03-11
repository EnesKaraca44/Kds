import pandas as pd
from datetime import datetime
from .baglanti import baglanti_olustur


def yabanci_hasta_verisi_yukle(start_date_str, end_date_str):
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    sql_query = """
        SELECT 
            suriye.HstNufus, suriye.HastaAdi, SUM(suriye.HstFiyat) AS Fiyat,
            suriye.hstgtrh, suriye.hstsra, suriye.HstUyruk, suriye.Ulke,
            suriye.GSS_TAKIP_NO, suriye.hsttetno, suriye.Cinsiyet, suriye.HstDtrh
        FROM (
            SELECT
                TblHasta.HstDtrh, TblHasta.HstUyruk, TblHasta.HstUlke,
                ISNULL(TBLULKE.AD, TblUyruk.ADI) AS Ulke,
                CASE TblHasta.Hstcins WHEN '0' THEN 'Erkek' WHEN '1' THEN 'Bayan' END AS Cinsiyet,
                TblHasta.HstAd + ' ' + TblHasta.HstSoy AS HastaAdi,
                TblHasta.HstKod, TblHastaRO.HstSra, TblHastaDetay.hsttetno,
                TblHastaDetay.HstFiyat, TblHasta.HstNufus, TblHastaRO.hstgtrh,
                TblHastaRO.GSS_TAKIP_NO
            FROM TblHasta (NOLOCK)
            LEFT JOIN TBLULKE (NOLOCK) ON ISNULL(TblHasta.HstUlke, 0) = TBLULKE.Id
            LEFT JOIN TblUyruk (NOLOCK) ON TblUyruk.KODU = TblHasta.HstUyruk
            INNER JOIN TblHastaRO (NOLOCK) ON TblHastaRO.HstKod = TblHasta.HstKod
            INNER JOIN TblHastaDetay (NOLOCK) ON TblHastaDetay.hstKod = TblHastaRO.HstKod 
                AND TblHastaDetay.Hstsra = TblHastaRO.HstSra 
                AND TblHastaDetay.HstGtrh = TblHastaRO.HstGtrh
            INNER JOIN tbltetkikdetay (NOLOCK) ON tbltetkikdetay.tkodu = TblHastaDetay.hsttetno 
                AND TblHastaDetay.HstSablon = tbltetkikdetay.tsablon
            WHERE TblHastaDetay.HstSilindi = 0
            AND (TblHastaRO.hstgtrh BETWEEN ? AND ?)
        ) AS suriye
        WHERE suriye.HstFiyat > 0
        AND ((suriye.HstUyruk <> 'TR' AND ISNULL(suriye.HstUyruk, '') <> '') OR suriye.Ulke NOT LIKE '%Türkiye%')
        GROUP BY 
            suriye.HstNufus, suriye.HastaAdi, suriye.hstgtrh, suriye.hstsra,
            suriye.HstUyruk, suriye.Ulke, suriye.GSS_TAKIP_NO, suriye.hsttetno,
            suriye.Cinsiyet, suriye.HstDtrh
        ORDER BY suriye.HastaAdi;
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
