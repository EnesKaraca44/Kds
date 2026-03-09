import pandas as pd
from .connection import get_db_connection


def load_sterilization_data(start_date_str, end_date_str):
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()

    sql_query = """
    ;WITH PaketToplamlari AS
    (
        SELECT 
            CksId, 
            SUM(PktAdet) AS ToplamPaket
        FROM TblStrCksDty WITH (NOLOCK)
        GROUP BY CksId
    ),
    HastaSayilari AS
    (
        SELECT 
            OdaID,
            CAST(KytTrh AS DATE) AS KytTarih,
            COUNT(DISTINCT CONCAT(HstId,'-',MrcNo)) AS HastaSayisi
        FROM TblStrHastaCks WITH (NOLOCK)
        WHERE KytTrh BETWEEN ? AND ?
          AND Striptal = 0
        GROUP BY 
            OdaID,
            CAST(KytTrh AS DATE)
    )
    SELECT 
        O.ODA_AD AS ServisAdi,
        S.KytZmn,
        SUM(ISNULL(PT.ToplamPaket, 0)) AS Toplam_Paket,
        SUM(ISNULL(PT.ToplamPaket, 0)) * 1.95 AS Toplam_Maliyet,
        ISNULL(HS.HastaSayisi, 0) AS Hasta_Sayisi
    FROM TblStrCks S WITH (NOLOCK)
    LEFT JOIN PaketToplamlari PT 
        ON PT.CksId = S.CksId
    LEFT JOIN HastaSayilari HS
        ON HS.OdaID = S.OdaId
       AND HS.KytTarih = CAST(S.KytZmn AS DATE)
    INNER JOIN TblODALAR O WITH (NOLOCK)
        ON O.ODA_ID = S.OdaId
    WHERE S.CksTrh BETWEEN ? AND ?
      AND S.CksSrvId = 37
      AND S.KlnkId IN (286,285,317,316,319,315,318,28)
      AND S.OdaId IN (
          1,2,3,4,5,6,8,9,10,11,12,13,14,15,16,17,18,19,20,
          21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,43,
          44,45,46,47,50,51,52,53,54,55,56,57,58,59,60,61,62,
          63,64,65,66,67,68,69,70,71,72,73,78,79,80,81,82,83,
          84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,
          101,102,103,104,105,106,107,108,109,110,111,112,113,
          114,115,116,117,118,119,120,121,122,123,124
      )
    GROUP BY 
        O.ODA_AD,
        S.KytZmn,
        HS.HastaSayisi
    ORDER BY 
        O.ODA_AD,
        S.KytZmn;
    """

    try:
        start_dt = f"{start_date_str} 00:00:00"
        end_dt = f"{end_date_str} 23:59:59"
        params = [start_dt, end_dt, start_dt, end_dt]

        df = pd.read_sql(sql_query, conn, params=params)
        if not df.empty:
            df['KytZmn'] = pd.to_datetime(df['KytZmn'])
        return df
    except Exception as e:
        print(f"❌ Sterilizasyon verisi yüklenirken hata: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
