import pandas as pd
from datetime import datetime
from .baglanti import baglanti_olustur


def fatura_gelir_verisi_yukle(start_date_str, end_date_str):
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    sql_query = """
        select 
f.FATURA_NO as FATURA_NO
,f.FATURA_TARIHI as FATURA_TARIHI 
, ck.CARI_KART_KODU as cariKartKodu
, ck.CARI_KART_ADI as cariKartAdi
, F.FATURA_TOPLAM_KDV + F.FATURA_TOPLAM_TUTAR as FATURA_KDVLI_TOPLAM_TUTAR 
,f.FATURA_ILGILI as FATURA_ILGILI
,f.FATURA_ACIKLAMA as FATURA_ACIKLAMA
,ckt.KURUM_TUR_TANIM  as KURUM_TURU
,f.FATURA_TOPLAM_TUTAR as FATURA_TOPLAM_TUTAR
,f.FATURA_TOPLAM_KDV as FATURA_TOPLAM_KDV 
,f.FATURA_KISI_SAYISI as FATURA_KISI_SAYISI
     from SBS_FATURA as f with(nolock) 
       left join SBS_FATURA_HASTA  as fh with(nolock) 
         on fh.SBS_FATURA_ID = f.SBS_FATURA_ID  and  ISNULL(fh.PSF_ID,0) = 0 
       left join  SBS_FATURA_HASTA_DETAY as sfhd with(nolock) 
         on sfhd.SBS_FATURA_HASTA_ID = fh.SBS_FATURA_HASTA_ID and ISNULL(sfhd.PSF_ID,0) = 0 
       left join  CARI_KART as ck  with(nolock) 
        on ck.CARI_KART_ID = f.FATURA_CARI_KART_ID and ISNULL(ck.PSF_ID,0) = 0 
       left join  CARI_KURUM_TUR as ckt  with(nolock) 
        on ck.CARI_KURUM_TURU  = ckt.KURUM_TUR_ID  and ISNULL(ckt.PSF_ID,0) = 0 
    where ISNULL(f.PSF_ID,0) = 0 
      and f.FATURA_TARIHI BETWEEN ? AND ?
   group by 
 f.FATURA_NO
,f.FATURA_TARIHI
, ck.CARI_KART_KODU 
, ck.CARI_KART_ADI
, F.FATURA_TOPLAM_KDV + F.FATURA_TOPLAM_TUTAR  
,f.FATURA_ILGILI 
,f.FATURA_ACIKLAMA
,ckt.KURUM_TUR_TANIM 
,f.FATURA_TOPLAM_TUTAR
,f.FATURA_TOPLAM_KDV 
,f.FATURA_KISI_SAYISI
    """

    try:
        start_dt = datetime.strptime(f'{start_date_str} 00:00:00', '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(f'{end_date_str} 23:59:59', '%Y-%m-%d %H:%M:%S')

        df = pd.read_sql(sql_query, conn, params=[start_dt, end_dt])
        if not df.empty:
            df['FATURA_TARIHI'] = pd.to_datetime(df['FATURA_TARIHI'])
        return df
    except Exception as e:
        print(f"❌ Kurum gelir verisi yüklenirken hata: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
