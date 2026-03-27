import pandas as pd
from datetime import datetime
from .baglanti import baglanti_olustur


def randevu_verisi_yukle(start_date_str, end_date_str):
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    sql_query = """
        SELECT
            SKS.SEVK_ID AS RandevuID,
            CAST(SKS.RANDEVU_OLUSTURMA_TRH AS DATE) AS BsvTrh,
            CAST(SKS.SEVK_ILK_CAGRILMA_TRH AS DATE) AS Trh,
            dbo.IntegerIntoTime(SKS.SEVK_RANDEVU_SAAT) AS Saat,
            H.HASTA_KODU AS HstKod,
            D.KIMLIK_ID AS DktID,
            SKS.SEVK_EDILEN_KLINIK_BIRIM_ID AS PolID,
            CASE WHEN ISNULL(SKS.SEVK_HST_GELIS_ID, 0) = 0 THEN 2 ELSE 1 END AS M_RANDEVU_DURUM,
            K.KIMLIK_TC_NO AS TC_KIMLIK_NO,
            TD.TAKVIM_OLAY_TUR_DETAY_ID AS RANDEVU_TURU_ID,
            CAST(NULL AS INT) AS M_RANDEVU_EKLEYEN,
            CASE WHEN ISNULL(SKS.PSF_ID, 0) = 0 THEN 0 ELSE 1 END AS IPTAL,
            DATEDIFF(
                DAY,
                CAST(SKS.RANDEVU_OLUSTURMA_TRH AS DATE),
                CAST(SKS.SEVK_ILK_CAGRILMA_TRH AS DATE)
            ) AS fark,
            TD.TAKVIM_OLAY_TUR_DETAY_ADI AS RANDEVU_TURU_ADI,
            B.BIRIM_AD AS SrvAd,
            D.DOKTOR_AD + ' ' + D.DOKTOR_SOYAD AS dktad,
            CAST(NULL AS NVARCHAR(20)) AS HstCepTel,
            CAST(NULL AS NVARCHAR(20)) AS tlfno,
            CASE
                WHEN ISNULL(SKS.SEVK_HST_GELIS_ID, 0) = 0 THEN 'Gelmedi'
                ELSE 'Geldi'
            END AS Durum,
            CAST(NULL AS INT) AS RANDEVU_TURU_GUN_LIMIT,
            TD.TAKVIM_OLAY_TUR_DETAY_ADI AS Randevuverilme_Yeri
        FROM SBS_KLINIK_SEVK AS SKS WITH (NOLOCK)
        LEFT JOIN KIMLIK AS K WITH (NOLOCK)
            ON SKS.HASTA_KIMLIK_ID = K.KIMLIK_ID
            AND ISNULL(K.PSF_ID, 0) = 0
        LEFT JOIN SBS_HASTA AS H WITH (NOLOCK)
            ON K.KIMLIK_ID = H.HASTA_KIMLIK_ID
            AND ISNULL(H.PSF_ID, 0) = 0
        LEFT JOIN SBS_DOKTOR AS D WITH (NOLOCK)
            ON SKS.SEVK_EDILEN_HEKIM_KIMLIK_ID = D.KIMLIK_ID
            AND ISNULL(D.PSF_ID, 0) = 0
        LEFT JOIN SBS_KLINIK AS SK WITH (NOLOCK)
            ON SKS.SEVK_EDILEN_KLINIK_BIRIM_ID = SK.BIRIM_ID
            AND ISNULL(SK.PSF_ID, 0) = 0
        LEFT JOIN BIRIM AS B WITH (NOLOCK)
            ON B.BIRIM_ID = SK.BIRIM_ID
            AND ISNULL(B.PSF_ID, 0) = 0
        LEFT JOIN PASIF AS P WITH (NOLOCK)
            ON P.PASIF_ID = SKS.PSF_ID
        LEFT JOIN TAKVIM_OLAY_TUR_DETAY AS TD WITH (NOLOCK)
            ON SKS.TAKVIM_OLAY_TUR_DETAY_ID = TD.TAKVIM_OLAY_TUR_DETAY_ID
            AND ISNULL(TD.PSF_ID, 0) = 0
        LEFT JOIN TAKVIM_OLAY_TUR AS T WITH (NOLOCK)
            ON TD.TAKVIM_OLAY_TUR_ID = T.TAKVIM_OLAY_TUR_ID
            AND ISNULL(T.PSF_ID, 0) = 0
        LEFT JOIN SBS_ODA_TANIM AS SKOT WITH (NOLOCK)
            ON SKOT.ODA_ID = SKS.ODA_ID
            AND ISNULL(SKOT.PSF_ID, 0) = 0
        WHERE (SKS.SEVK_TURU & 4) = 4
          AND ISNULL(SKS.PSF_ID, 0) = 0
          AND SKS.SEVK_ILK_CAGRILMA_TRH >= ?
          AND SKS.SEVK_ILK_CAGRILMA_TRH <  DATEADD(DAY, 1, ?)
    """

    try:
        start_dt = datetime.strptime(f'{start_date_str} 00:00:00', '%Y-%m-%d %H:%M:%S')
        # SQL sorgusu zaten "< DATEADD(DAY, 1, ?)" yapıyor.
        # Bu yüzden Python tarafında end_dt 00:00:00 olmalı ki örneğin 18 Mart seçildiğinde 19 Mart 00:00:00'dan küçük olanları (tüm 18 Mart'ı) garantili alsın.
        end_dt = datetime.strptime(f'{end_date_str} 00:00:00', '%Y-%m-%d %H:%M:%S')

        df = pd.read_sql(sql_query, conn, params=[start_dt, end_dt])
        df['BsvTrh'] = pd.to_datetime(df['BsvTrh'])
        df['Trh'] = pd.to_datetime(df['Trh'])
        return df
    except Exception as e:
        print(f"❌ Randevu verisi yüklenirken hata: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
