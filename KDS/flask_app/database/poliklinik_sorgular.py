import pandas as pd
from datetime import datetime
from .baglanti import baglanti_olustur


def poliklinik_performans_verisi_yukle(start_date_str, end_date_str):
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    sql_query = """
        SELECT
            TblHasta.HstAd + ' ' + TblHasta.HstSoy AS ADI_SOYADI,
            ISNULL(TblServis.SrvAd,'BELİRTİLMEMİŞ') AS SrvAd,
            ISNULL(TblDoktor.DktAd,'BELİRTİLMEMİŞ') AS DOKTOR_ADI,
            tbpd.HstKod, tbpd.Saat, tbpd.Trh AS KAYIT_TARIHI,
            tbpd.HstGelisNo, tbpd.HstGelisTrh, 1 AS ADET,
            tk.KrmAdi, tbpd.DoktorId, TblDoktor.DkTKAd
        FROM TblPolDefterDoktor tbpd (NOLOCK)
        INNER JOIN TblHasta (NOLOCK) ON tbpd.HstKod = TblHasta.HstKod
        LEFT OUTER JOIN TblDoktor (NOLOCK) ON tbpd.DoktorID = TblDoktor.DktNo
        LEFT OUTER JOIN TblServis (NOLOCK) ON tbpd.PolID = TblServis.SrvNo
        LEFT OUTER JOIN TblHastaRO thr (NOLOCK) ON THR.HstKod = tbpd.HstKod AND thr.HstSra = tbpd.HstGelisNo AND thr.HstGtrh = tbpd.HstGelisTrh
        LEFT OUTER JOIN TblKurum tk (NOLOCK) ON tk.KrmKodu = thr.HstKurum
        WHERE ((ISNULL(tbpd.ID_FLAG,2) & 6)= 2 Or (ISNULL(tbpd.ID_FLAG,2) & 6)= 4 Or (ISNULL(tbpd.ID_FLAG,2) & 6)= 6)
        AND tbpd.PolID IN (SELECT SrvNo FROM TblServis WHERE ISNULL(DEFTER_SRA_POLDR,0) = 1)
        AND ISNULL(thr.HstSilindi,0)=0 AND (tbpd.Trh BETWEEN ? AND ?)

        UNION ALL

        SELECT
            TblHasta.HstAd + ' ' + TblHasta.HstSoy AS ADI_SOYADI,
            ISNULL(TblServis.SrvAd,'BELİRTİLMEMİŞ') AS SrvAd,
            ISNULL(TblDoktor.DktAd,'BELİRTİLMEMİŞ') AS DOKTOR_ADI,
            tbpd.HstKod, tbpd.Saat, tbpd.Trh AS KAYIT_TARIHI,
            tbpd.HstGelisNo, tbpd.HstGelisTrh, 1 AS ADET,
            tk.KrmAdi, tbpd.DoktorId, TblDoktor.DkTKAd
        FROM TblPolDefter tbpd (NOLOCK)
        INNER JOIN TblHasta (NOLOCK) ON tbpd.HstKod = TblHasta.HstKod
        LEFT OUTER JOIN TblDoktor (NOLOCK) ON tbpd.DoktorID = TblDoktor.DktNo
        LEFT OUTER JOIN TblServis (NOLOCK) ON tbpd.PolID = TblServis.SrvNo
        LEFT OUTER JOIN TblHastaRO thr (NOLOCK) ON THR.HstKod = tbpd.HstKod AND thr.HstSra = tbpd.HstGelisNo AND thr.HstGtrh = tbpd.HstGelisTrh
        LEFT OUTER JOIN TblKurum tk (NOLOCK) ON tk.KrmKodu = thr.HstKurum
        WHERE ((ISNULL(tbpd.ID_FLAG,2) & 6)= 2 Or (ISNULL(tbpd.ID_FLAG,2) & 6)= 4 Or (ISNULL(tbpd.ID_FLAG,2) & 6)= 6)
        AND tbpd.PolID IN (SELECT SrvNo FROM TblServis WHERE ISNULL(DEFTER_SRA_POLDR,0) = 0)
        AND ISNULL(thr.HstSilindi,0)=0 AND (tbpd.Trh BETWEEN ? AND ?)
    """

    try:
        start_dt = datetime.strptime(f'{start_date_str} 00:00:00', '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(f'{end_date_str} 23:59:59', '%Y-%m-%d %H:%M:%S')

        df = pd.read_sql(sql_query, conn, params=[start_dt, end_dt, start_dt, end_dt])
        df['KAYIT_TARIHI'] = pd.to_datetime(df['KAYIT_TARIHI'])
        df['HstGelisTrh'] = pd.to_datetime(df['HstGelisTrh'])
        return df
    except Exception as e:
        print(f"❌ Poliklinik verisi yüklenirken hata: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
