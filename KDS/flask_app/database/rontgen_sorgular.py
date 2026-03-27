import pandas as pd
from .baglanti import baglanti_olustur

def rontgen_verisi_hekim_brans(start_date_str, end_date_str):
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame(), pd.DataFrame()

    try:
        sql_hekim = f"""
        select
        isnull(sd.DOKTOR_AD + ' ' + sd.DOKTOR_SOYAD,'Belirtilmemiş') as DktAd,
        sum(case when skh.RECETE_GRUP_ID =3 then cast(shh.HST_MIKTAR as float) else 0 end) as Periapikal,
        sum(case when skh.RECETE_GRUP_ID =4 then cast(shh.HST_MIKTAR as float) else 0 end) as Panoramik,
        sum(case when skh.RECETE_GRUP_ID =5 then cast(shh.HST_MIKTAR as float) else 0 end) as Sefalometrik,
        sum(case when skh.RECETE_GRUP_ID =6 then cast(shh.HST_MIKTAR as float) else 0 end) as DentalTomografi
        from SBS_HASTA_HAREKET  as shh
        inner join  SBS_HASTA_RESMI_UCRETLI  as shru  with (nolock)   on shru.HST_GELIS_ID =shh.HST_GELIS_ID  AND isnull(shh.PSF_ID ,0)=0
        inner join KIMLIK as Km with (nolock) on km.KIMLIK_ID = shru.HASTA_KIMLIK_ID and isnull(Km.PSF_ID,0)=0
        inner join SBS_HASTA as sh with (nolock) on sh.HASTA_KIMLIK_ID = km.KIMLIK_ID and isnull(sh.PSF_ID,0)=0
        inner join BIRIM AS B on B.BIRIM_ID =shru.HST_BIRIM_ID   and isnull(sh.PSF_ID,0)=0
        inner join SBS_KLINIK AS SK on SK.BIRIM_ID  =B.BIRIM_ID   and isnull(sk.PSF_ID,0)=0
        left join SBS_DOKTOR AS SD on SD.KIMLIK_ID = shru.HEKIM_KIMLIK_ID and isnull(SD.PSF_ID, 0) = 0
        left join SBS_DOKTOR as sdt with(nolock) ON sdt.KIMLIK_ID = shh.TEKNISYEN_KIMLIK_ID and ISNULL(sdt.PSF_ID, 0) = 0 
        inner join STOK_KART_HIZMET as skh  with (nolock) on skh.STOK_ID =shh.STOK_ID and isnull(skh.PSF_ID, 0) = 0
        left join CARI_KART as ck with(nolock)  on ck.CARI_KART_ID=shru.HST_KURUM_ID and (isnull(ck.PSF_ID, 0) = 0)
        left join TUR_DETAY as TD with(nolock) ON TD.TUR_DETAY_ID = SK.KLINIK_TUR_ID and ISNULL(TD.PSF_ID, 0) = 0 AND TD.TUR_ID = 470004
        where isnull(shru.PSF_ID, 0) = 0
        AND isnull(SD.PSF_ID, 0) = 0 
        AND isnull(B.PSF_ID, 0) = 0
        and shh.ISLEM_TRH >= '{start_date_str}' 
        and shh.ISLEM_TRH <= '{end_date_str}' 
        and skh.RECETE_GRUP_ID IN(3, 4, 5, 6)
        group by isnull(sd.DOKTOR_AD + ' ' + sd.DOKTOR_SOYAD, 'Belirtilmemiş') 
        order by isnull(sd.DOKTOR_AD + ' ' + sd.DOKTOR_SOYAD, 'Belirtilmemiş')
        """

        sql_brans = f"""
        select
        isnull(BR.BRANS_AD  ,'Belirtilmemiş') as BirimAd,
        sum(case when skh.RECETE_GRUP_ID =3 then cast(shh.HST_MIKTAR as float) else 0 end) as Periapikal,
        sum(case when skh.RECETE_GRUP_ID =4 then cast(shh.HST_MIKTAR as float) else 0 end) as Panoramik,
        sum(case when skh.RECETE_GRUP_ID =5 then cast(shh.HST_MIKTAR as float) else 0 end) as Sefalometrik,
        sum(case when skh.RECETE_GRUP_ID =6 then cast(shh.HST_MIKTAR as float) else 0 end) as DentalTomografi
        from SBS_HASTA_HAREKET  as shh
        inner join  SBS_HASTA_RESMI_UCRETLI  as shru  with (nolock)   on shru.HST_GELIS_ID =shh.HST_GELIS_ID  AND isnull(shh.PSF_ID ,0)=0
        inner join KIMLIK as Km with (nolock) on km.KIMLIK_ID = shru.HASTA_KIMLIK_ID and isnull(Km.PSF_ID,0)=0
        inner join SBS_HASTA as sh with (nolock) on sh.HASTA_KIMLIK_ID = km.KIMLIK_ID and isnull(sh.PSF_ID,0)=0
        inner join BIRIM AS B on B.BIRIM_ID =shru.HST_BIRIM_ID   and isnull(sh.PSF_ID,0)=0
        inner join SBS_KLINIK AS SK on SK.BIRIM_ID  =B.BIRIM_ID   and isnull(sk.PSF_ID,0)=0
        left join SBS_DOKTOR AS SD on SD.KIMLIK_ID  =shru.HEKIM_KIMLIK_ID and isnull(SD.PSF_ID,0)=0
        left join BRANS AS BR on BR.BRANS_ID   =SK.BRANS_ID    and isnull(BR.PSF_ID,0)=0
        inner join STOK_KART_HIZMET as skh  with (nolock) on skh.STOK_ID =shh.STOK_ID and isnull(skh.PSF_ID,0)=0
        left join CARI_KART as ck with(nolock)  on ck.CARI_KART_ID=shru.HST_KURUM_ID and (isnull(ck.PSF_ID,0)= 0)
        left join TUR_DETAY   as TD with(nolock) ON TD.TUR_DETAY_ID  =SK.KLINIK_TUR_ID   and ISNULL(TD.PSF_ID,0) = 0  AND TD.TUR_ID =470004
        left join SBS_DOKTOR as sdt with(nolock) ON sdt.KIMLIK_ID = shh.TEKNISYEN_KIMLIK_ID and ISNULL(sdt.PSF_ID, 0) = 0 
        where isnull(shru.PSF_ID, 0) = 0
        AND isnull(B.PSF_ID, 0) = 0
        and shh.ISLEM_TRH >= '{start_date_str}' 
        and shh.ISLEM_TRH <= '{end_date_str}' 
        and skh.RECETE_GRUP_ID IN(3,4,5,6)
        group by isnull(BR.BRANS_AD ,'Belirtilmemiş') 
        order by isnull(BR.BRANS_AD ,'Belirtilmemiş')
        """

        df_hekim = pd.read_sql(sql_hekim, conn).copy()
        df_brans = pd.read_sql(sql_brans, conn).copy()
        return df_hekim, df_brans
    except Exception as e:
        print(f"❌ Radyoloji sorgu hatası: {e}")
        return pd.DataFrame(), pd.DataFrame()
    finally:
        conn.close()
