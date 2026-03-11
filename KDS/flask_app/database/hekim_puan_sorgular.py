import pandas as pd
from .baglanti import baglanti_olustur


def hekim_puan_verisi_yukle(start_date, end_date):
    conn = baglanti_olustur()
    if not conn:
        return None

    query = """
    SET NOCOUNT ON; 
    DECLARE @BAS_DATE DATE = ?;
    DECLARE @BIT_DATE DATE = ?;

    WITH RawData AS (
        SELECT  
            VW_HASTANE.TETKIK_DOKTOR_ADI,
            VW_HASTANE.HASTA_KODU,
            VW_HASTANE.HASTA_ADI_SOYADI,
            VW_HASTANE.HASTA_GELIS_NO,
            VW_HASTANE.HASTA_GELIS_TARIHI,
            VW_HASTANE.TETKIK_TARIHI,
            VW_HASTANE.TETKIK_ADI,
            VW_HASTANE.TETKIK_ADET,
            VW_HASTANE.TETKIK_DOKTOR_ID,
            LEFT(VW_HASTANE.TETKIK_SAATI, 5) AS TETKIK_SAATI,
            VW_HASTANE.TETKIK_BUTCE_KODU,
            TblDoktor.DktMuaynehane,
            VW_HASTANE.TETKIK_DIS_NO,
            VW_HASTANE.TETKIK_BIRIM_UCRET,
            VW_HASTANE.MESAI_DISI,
            TblDoktor.DkTkAd,
            TblDoktor.DOKTOR_TCK_NO,
            Kons.DktAd AS KonAd,
            ISNULL(NULLIF(VW_HASTANE.RntTur, 0) * SIGN(ISNULL(VW_HASTANE.RADYODOKTOR, 0)) +
                   NULLIF(VW_HASTANE.HstTeknisyen, -32768) - VW_HASTANE.HstTeknisyen, 1) AS Katsayi,
            VW_HASTANE.TETKIK_BIRIM_PUAN
        FROM VW_HASTANE WITH (NOLOCK)
        INNER JOIN TblDoktor WITH (NOLOCK) ON VW_HASTANE.TETKIK_DOKTOR_ID = TblDoktor.DktNo
        LEFT JOIN TblDoktor AS Kons WITH (NOLOCK) ON VW_HASTANE.T_DOKTOR2_ID = Kons.DktNo
        WHERE VW_HASTANE.TETKIK_BIRIM_PUAN > 0 
          AND VW_HASTANE.TETKIK_TARIHI BETWEEN @BAS_DATE AND @BIT_DATE
    )
    SELECT 
        TETKIK_DOKTOR_ADI, HASTA_KODU, HASTA_ADI_SOYADI, HASTA_GELIS_NO,
        HASTA_GELIS_TARIHI, TETKIK_TARIHI, TETKIK_ADI, TETKIK_DOKTOR_ID,
        TETKIK_SAATI, TETKIK_BUTCE_KODU, DktMuaynehane, TETKIK_DIS_NO,
        TETKIK_BIRIM_UCRET, MESAI_DISI, DkTkAd, DOKTOR_TCK_NO, KonAd,
        SUM(TETKIK_ADET) AS TETKIK_ADET,
        MIN(Katsayi * Katsayi * TETKIK_BIRIM_PUAN) AS PUAN,
        SUM(TETKIK_ADET) * MIN(Katsayi * Katsayi * TETKIK_BIRIM_PUAN) AS TETKIK_TOPLAM_PUAN
    FROM RawData
    GROUP BY 
        TETKIK_DOKTOR_ADI, HASTA_KODU, HASTA_ADI_SOYADI, HASTA_GELIS_NO,
        HASTA_GELIS_TARIHI, TETKIK_TARIHI, TETKIK_ADI, TETKIK_DOKTOR_ID,
        TETKIK_SAATI, TETKIK_BUTCE_KODU, DktMuaynehane, TETKIK_DIS_NO,
        TETKIK_BIRIM_UCRET, MESAI_DISI, DkTkAd, DOKTOR_TCK_NO, KonAd
    ORDER BY TETKIK_DOKTOR_ADI, TETKIK_ADI;
    """

    try:
        df = pd.read_sql(query, conn, params=(start_date, end_date))
        return df
    except Exception as e:
        print(f"Hekim Puan Verisi Yükleme Hatası: {e}")
        return None
    finally:
        conn.close()
