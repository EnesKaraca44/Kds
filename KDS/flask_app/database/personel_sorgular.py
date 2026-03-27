import pandas as pd
from .baglanti import baglanti_olustur

# Personel Sorgulama ile ilgili SQL sorguları bu dosyada toplanacaktır.

def get_personel_calisma_durumu_ozet(start_date, end_date):
    """Personel çalışma durumu özet verilerini (sayıları) getirir."""
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()
    
    try:
        sql = f"""
        SELECT data1 as data1, COUNT(1) AS data2 FROM  (
           select
             CASE WHEN ISNULL(GK.IC_BIRIM,1) = 0 AND ISNULL(KK.IC_BIRIM,1) = 1 THEN 'GEÇİCİ GÖREVLİ GİDEN'
                  WHEN CALISMA.DURUM = 'RAPORLU' THEN 'RAPORLU' 
                WHEN CALISMA.DURUM = 'İZİNLİ' THEN 'İZİNLİ'
                ELSE 'ÇALIŞIYOR'
             END AS data1
            from KIMLIK as kmlk
           inner join PERSONEL AS p
              on kmlk.KIMLIK_ID =p.KIMLIK_ID
            left outer join ( select sum(CALISMA_GUN) as CALISMA_GUN, sum(UCRETSIZ_IZIN_GUN) as UCRETSIZ_IZIN_GUN, sum(IZIN_GUN) as IZIN_GUN, c.KIMLIK_ID, HID,
                     case when td.TUR_DEGER_KOD = 'RAPORLUIZIN' OR td.TUR_DEGER_KOD = 'TEKTABIPRAPORU' OR td.TUR_DEGER_KOD = 'HEYETRAPORU' THEN 'RAPORLU'
                        when td.TUR_DEGER_KOD <> '' then 'İZİNLİ' ELSE null end as DURUM
                         from fnTbl_KIMLIK_HAREKET_CALISMA('{start_date}', '{end_date}', '2075-01-01') as c
                     left join KIMLIK_HAREKET as kh on kh.KIMLIK_HAREKET_ID = c.HID
                     left join IZIN as i on i.IZIN_ID = kh.IZIN_ID
                     left join TUR_DETAY as td on td.TUR_DETAY_ID = i.IZIN_TUR_ID
                        group by c.KIMLIK_ID, HID, IZIN_TUR_ID, td.TUR_DEGER_KOD) AS CALISMA
              on CALISMA.KIMLIK_ID = kmlk.KIMLIK_ID
           inner join KIMLIK_HAREKET as kh
              on kh.KIMLIK_ID=kmlk.KIMLIK_ID and CALISMA.HID=kh.KIMLIK_HAREKET_ID
            left outer join IZIN as i
            on i.IZIN_ID= kh.IZIN_ID
            left outer join TUR_DETAY as td
            on td.TUR_DETAY_ID=i.IZIN_TUR_ID
            left outer join (select fnKh.KIMLIK_ID, kig.GOREV_KURUM_ID, kig.GOREV_BIRIM_ID, kig.GOREV_UNVAN_ID, kig.GOREV_BRANS_ID, BIRIM.BIRIM_AD, BIRIM.BIRIM_ID, BIRIM.UST_BIRIM_ID
                           from KIMLIK_HAREKET as kh
                          inner join (select KIMLIK_ID, HID
                                  from fnTbl_KIMLIK_HAREKET('{start_date}', DATEADD(DAY,1,'{end_date}'), '2075-01-01')
                                 group by KIMLIK_ID, HID) as fnKh
                           on (fnKh.HID = kh.KIMLIK_HAREKET_ID)
                          inner join KIMLIK_IS_GECMISI as kig
                           on (isnull(kh.IS_GECMISI_ID, kh.UCRETSIZ_IZIN_ID) = kig.IS_GECMISI_ID)
                       left join BIRIM
                       on BIRIM.BIRIM_ID=kig.GOREV_KURUM_ID
                          where (isnull(kh.PSF_ID, 0) = 0)
                          and (isnull(kig.PSF_ID, 0) = 0)) AS g
              on kmlk.KIMLIK_ID=g.KIMLIK_ID
            left outer join BIRIM as kk
              on (p.KADRO_KURUM_ID = kk.BIRIM_ID)
            left outer join UNVAN as ku
              on (p.KADRO_UNVAN_ID = ku.UNVAN_ID)
            left outer join BIRIM as gk
              on (g.GOREV_KURUM_ID = gk.BIRIM_ID)
            left outer join UNVAN as gu
              on (g.GOREV_UNVAN_ID = gu.UNVAN_ID)
           where (isnull(p.PSF_ID, 0) = 0)
             and (isnull(kh.PSF_ID, 0) = 0)
             and (isnull(kk.PSF_ID, 0) = 0)
             and (isnull(gk.PSF_ID, 0) = 0)
             and (isnull(gu.PSF_ID, 0) = 0)
             and (isnull(ku.PSF_ID, 0) = 0)
             and (isnull(kmlk.PSF_ID, 0) = 0)
           and (kk.IC_BIRIM = 1 or gk.IC_BIRIM = 1)
             and (kk.BIRIM_OZELLIK is null or kk.BIRIM_OZELLIK & 1 = 1)
             and (gk.BIRIM_OZELLIK is null or gk.BIRIM_OZELLIK & 1 = 1)
           ) AS CALISMA
           GROUP BY data1
        """
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        print(f"❌ Personel özet sorgu hatası: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_personel_calisma_durumu_detay(start_date, end_date, calisma_tur=None):
    """Personel çalışma durumu detay listesini getirir."""
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()
    
    try:
        calisma_tur_filter = f"'{calisma_tur}'" if calisma_tur else "NULL"
        
        sql = f"""
        select dataId, data1, data3, data4, DURUM FROM (
          select kmlk.KIMLIK_ID as dataId, kmlk.KIMLIK_AD + ' ' + kmlk.KIMLIK_SOYAD AS data1,
                 gk.BIRIM_AD as data3,
                 isnull(gu.UNVAN_AD,ku.UNVAN_AD) as data4,
              CASE WHEN ISNULL(GK.IC_BIRIM,1) = 0 AND ISNULL(KK.IC_BIRIM,1) = 1 THEN 'GEÇİCİ GÖREVLİ GİDEN'
                  WHEN CALISMA.DURUM = 'RAPORLU' THEN 'RAPORLU' 
                WHEN CALISMA.DURUM = 'İZİNLİ' THEN 'İZİNLİ'
                ELSE 'ÇALIŞIYOR'
             END AS DURUM 
            from KIMLIK as kmlk
           inner join PERSONEL AS p
              on kmlk.KIMLIK_ID =p.KIMLIK_ID
            left outer join ( select sum(CALISMA_GUN) as CALISMA_GUN, sum(UCRETSIZ_IZIN_GUN) as UCRETSIZ_IZIN_GUN, sum(IZIN_GUN) as IZIN_GUN, c.KIMLIK_ID, HID, 
                     case when td.TUR_DEGER_KOD = 'RAPORLUIZIN' OR td.TUR_DEGER_KOD = 'TEKTABIPRAPORU' OR td.TUR_DEGER_KOD = 'HEYETRAPORU' THEN 'RAPORLU'
                        when td.TUR_DEGER_KOD <> '' then 'İZİNLİ' ELSE null end as DURUM
                         from fnTbl_KIMLIK_HAREKET_CALISMA('{start_date}', '{end_date}', '2075-01-01') as c
                     left join KIMLIK_HAREKET as kh on kh.KIMLIK_HAREKET_ID = c.HID
                     left join IZIN as i on i.IZIN_ID = kh.IZIN_ID
                     left join TUR_DETAY as td on td.TUR_DETAY_ID = i.IZIN_TUR_ID
                        group by c.KIMLIK_ID, HID, IZIN_TUR_ID, td.TUR_DEGER_KOD) AS CALISMA
              on CALISMA.KIMLIK_ID = kmlk.KIMLIK_ID
           inner join KIMLIK_HAREKET as kh
              on kh.KIMLIK_ID=kmlk.KIMLIK_ID and CALISMA.HID=kh.KIMLIK_HAREKET_ID
            left outer join IZIN as i
            on i.IZIN_ID= kh.IZIN_ID
            left outer join TUR_DETAY as td
            on td.TUR_DETAY_ID=i.IZIN_TUR_ID
            left outer join (select fnKh.KIMLIK_ID, kig.GOREV_KURUM_ID, kig.GOREV_BIRIM_ID, kig.GOREV_UNVAN_ID, kig.GOREV_BRANS_ID, BIRIM.BIRIM_AD, BIRIM.BIRIM_ID, BIRIM.UST_BIRIM_ID
                           from KIMLIK_HAREKET as kh
                          inner join (select KIMLIK_ID, HID
                                  from fnTbl_KIMLIK_HAREKET('{start_date}', DATEADD(DAY,1,'{end_date}'), '2075-01-01')
                                 group by KIMLIK_ID, HID) as fnKh
                           on (fnKh.HID = kh.KIMLIK_HAREKET_ID)
                          inner join KIMLIK_IS_GECMISI as kig
                           on (isnull(kh.IS_GECMISI_ID, kh.UCRETSIZ_IZIN_ID) = kig.IS_GECMISI_ID)
                       left join BIRIM
                       on BIRIM.BIRIM_ID=kig.GOREV_KURUM_ID
                          where (isnull(kh.PSF_ID, 0) = 0)
                          and (isnull(kig.PSF_ID, 0) = 0)) AS g
              on kmlk.KIMLIK_ID=g.KIMLIK_ID
            left outer join BIRIM as kk
              on (p.KADRO_KURUM_ID = kk.BIRIM_ID)
            left outer join UNVAN as ku
              on (p.KADRO_UNVAN_ID = ku.UNVAN_ID)
            left outer join BIRIM as gk
              on (g.GOREV_KURUM_ID = gk.BIRIM_ID)
            left outer join UNVAN as gu
              on (g.GOREV_UNVAN_ID = gu.UNVAN_ID)
           where (isnull(p.PSF_ID, 0) = 0)
             and (isnull(kh.PSF_ID, 0) = 0)
             and (isnull(kk.PSF_ID, 0) = 0)
             and (isnull(gk.PSF_ID, 0) = 0)
             and (isnull(gu.PSF_ID, 0) = 0)
             and (isnull(ku.PSF_ID, 0) = 0)
             and (isnull(kmlk.PSF_ID, 0) = 0)
           and (kk.IC_BIRIM = 1 or gk.IC_BIRIM = 1)
             and (kk.BIRIM_OZELLIK is null or kk.BIRIM_OZELLIK & 1 = 1)
             and (gk.BIRIM_OZELLIK is null or gk.BIRIM_OZELLIK & 1 = 1)
        ) as CALISMA  
           WHERE ({calisma_tur_filter} is null or CALISMA.DURUM = {calisma_tur_filter})
          order by data1
        """
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        print(f"❌ Personel detay sorgu hatası: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_personel_kadro_unvan_ozet(start_date, end_date):
    """Kadro unvanı bazlı personel sayılarını getirir."""
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()
    
    try:
        sql = f"""
        SELECT data1, COUNT(1) AS data2 FROM  (
          select
            isnull(ku.UNVAN_AD,'-') as data1
            from KIMLIK as kmlk
           inner join PERSONEL AS p
              on kmlk.KIMLIK_ID =p.KIMLIK_ID
           inner join (select fnKh.KIMLIK_ID, kig.GOREV_KURUM_ID, kig.GOREV_BIRIM_ID, kig.GOREV_UNVAN_ID, kig.GOREV_BRANS_ID, BIRIM.BIRIM_AD, BIRIM.BIRIM_ID, BIRIM.UST_BIRIM_ID
                           from KIMLIK_HAREKET as kh
                          inner join (select KIMLIK_ID, HID
                                  from fnTbl_KIMLIK_HAREKET('{start_date}', DATEADD(DAY,1,'{end_date}'), '2075-01-01')
                                 group by KIMLIK_ID, HID) as fnKh
                           on (fnKh.HID = kh.KIMLIK_HAREKET_ID)
                          inner join KIMLIK_IS_GECMISI as kig
                           on (isnull(kh.IS_GECMISI_ID, kh.UCRETSIZ_IZIN_ID) = kig.IS_GECMISI_ID)
                       left join BIRIM
                       on BIRIM.BIRIM_ID=kig.GOREV_KURUM_ID
                          where (isnull(kh.PSF_ID, 0) = 0)
                          and (isnull(kig.PSF_ID, 0) = 0)) AS g
              on kmlk.KIMLIK_ID=g.KIMLIK_ID
            left outer join BIRIM as kk
              on (p.KADRO_KURUM_ID = kk.BIRIM_ID)
            left outer join UNVAN as ku
              on (p.KADRO_UNVAN_ID = ku.UNVAN_ID)
            left outer join BIRIM as gk
              on (g.GOREV_KURUM_ID = gk.BIRIM_ID)
            left outer join UNVAN as gu
              on (g.GOREV_UNVAN_ID = gu.UNVAN_ID)
          left outer join BIRIM as gb
              on (g.GOREV_BIRIM_ID = gb.BIRIM_ID)
          left outer join BIRIM as ub
              on (ub.BIRIM_ID = gb.UST_BIRIM_ID)
           where (isnull(p.PSF_ID, 0) = 0)
             and (isnull(kmlk.PSF_ID, 0) = 0)
           and (kk.IC_BIRIM = 1 or gk.IC_BIRIM = 1)
           ) AS CALISMA
           GROUP BY data1
        """
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        print(f"❌ Kadro unvan özet sorgu hatası: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_personel_kadro_unvan_detay(start_date, end_date, kadro_unvan=None):
    """Kadro unvanı bazlı personel detay listesini getirir."""
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()
    
    try:
        kadro_filter = f"'{kadro_unvan}'" if kadro_unvan else "NULL"
        
        sql = f"""
        select dataId, data1, data3, data4, data5 FROM (
          select kmlk.KIMLIK_ID as dataId, kmlk.KIMLIK_AD + ' ' + kmlk.KIMLIK_SOYAD AS data1,
                 gk.BIRIM_AD as data3,
                 gu.UNVAN_AD as data4, isnull(ku.UNVAN_AD,'-') as data5
              from KIMLIK as kmlk
           inner join PERSONEL AS p
              on kmlk.KIMLIK_ID =p.KIMLIK_ID
           inner join (select fnKh.KIMLIK_ID, kig.GOREV_KURUM_ID, kig.GOREV_BIRIM_ID, kig.GOREV_UNVAN_ID, kig.GOREV_BRANS_ID, BIRIM.BIRIM_AD, BIRIM.BIRIM_ID, BIRIM.UST_BIRIM_ID
                           from KIMLIK_HAREKET as kh
                          inner join (select KIMLIK_ID, HID
                                  from fnTbl_KIMLIK_HAREKET('{start_date}', DATEADD(DAY,1,'{end_date}'), '2075-01-01')
                                 group by KIMLIK_ID, HID) as fnKh
                           on (fnKh.HID = kh.KIMLIK_HAREKET_ID)
                          inner join KIMLIK_IS_GECMISI as kig
                           on (isnull(kh.IS_GECMISI_ID, kh.UCRETSIZ_IZIN_ID) = kig.IS_GECMISI_ID)
                       left join BIRIM
                       on BIRIM.BIRIM_ID=kig.GOREV_KURUM_ID
                          where (isnull(kh.PSF_ID, 0) = 0)
                          and (isnull(kig.PSF_ID, 0) = 0)) AS g
              on kmlk.KIMLIK_ID=g.KIMLIK_ID
            left outer join BIRIM as kk
              on (p.KADRO_KURUM_ID = kk.BIRIM_ID)
            left outer join UNVAN as ku
              on (p.KADRO_UNVAN_ID = ku.UNVAN_ID)
            left outer join BIRIM as gk
              on (g.GOREV_KURUM_ID = gk.BIRIM_ID)
            left outer join UNVAN as gu
              on (g.GOREV_UNVAN_ID = gu.UNVAN_ID)
           where (isnull(p.PSF_ID, 0) = 0)
             and (isnull(kmlk.PSF_ID, 0) = 0)
           and (kk.IC_BIRIM = 1 or gk.IC_BIRIM = 1)
        ) as CALISMA  
        WHERE ({kadro_filter} is null or CALISMA.data5 = {kadro_filter})
        order by data1
        """
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        print(f"❌ Kadro unvan detay sorgu hatası: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_personel_tur_ozet(start_date, end_date):
    """Personel türü bazlı sayıları getirir."""
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()
    
    try:
        sql = f"""
        SELECT data1, COUNT(1) AS data2 FROM  (
          select
            isnull(pt.PERSONEL_TUR_AD,'-' ) as data1
            from KIMLIK as kmlk
           inner join PERSONEL AS p
              on kmlk.KIMLIK_ID =p.KIMLIK_ID
           inner join (select fnKh.KIMLIK_ID, kig.GOREV_KURUM_ID, kig.GOREV_BIRIM_ID, kig.GOREV_UNVAN_ID, kig.GOREV_BRANS_ID, BIRIM.BIRIM_AD, BIRIM.BIRIM_ID, BIRIM.UST_BIRIM_ID
                           from KIMLIK_HAREKET as kh
                          inner join (select KIMLIK_ID, HID
                                  from fnTbl_KIMLIK_HAREKET('{start_date}', DATEADD(DAY,1,'{end_date}'), '2075-01-01')
                                 group by KIMLIK_ID, HID) as fnKh
                           on (fnKh.HID = kh.KIMLIK_HAREKET_ID)
                          inner join KIMLIK_IS_GECMISI as kig
                           on (isnull(kh.IS_GECMISI_ID, kh.UCRETSIZ_IZIN_ID) = kig.IS_GECMISI_ID)
                       left join BIRIM
                       on BIRIM.BIRIM_ID=kig.GOREV_KURUM_ID
                          where (isnull(kh.PSF_ID, 0) = 0)
                          and (isnull(kig.PSF_ID, 0) = 0)) AS g
              on kmlk.KIMLIK_ID=g.KIMLIK_ID
            left outer join BIRIM as kk
              on (p.KADRO_KURUM_ID = kk.BIRIM_ID)
            left outer join UNVAN as ku
              on (p.KADRO_UNVAN_ID = ku.UNVAN_ID)
            left outer join BIRIM as gk
              on (g.GOREV_KURUM_ID = gk.BIRIM_ID)
            left outer join UNVAN as gu
              on (g.GOREV_UNVAN_ID = gu.UNVAN_ID)
          left outer join PERSONEL_TUR as pt
              on (p.PERSONEL_TUR_ID = pt.PERSONEL_TUR_ID)
           where (isnull(p.PSF_ID, 0) = 0)
             and (isnull(kmlk.PSF_ID, 0) = 0)
           and (kk.IC_BIRIM = 1 or gk.IC_BIRIM = 1)
           ) AS CALISMA
           GROUP BY data1
        """
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        print(f"❌ Personel tür özet sorgu hatası: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_personel_tur_detay(start_date, end_date, personel_tur=None):
    """Personel türü bazlı detay listesini getirir."""
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()
    
    try:
        tur_filter = f"'{personel_tur}'" if personel_tur else "NULL"
        
        sql = f"""
        select dataId, data1, data3, data4 FROM (
          select kmlk.KIMLIK_ID as dataId, kmlk.KIMLIK_AD + ' ' + kmlk.KIMLIK_SOYAD AS data1,
                 gk.BIRIM_AD  as data3, isnull(pt.PERSONEL_TUR_AD, '-') as data5,
                 isnull(gu.UNVAN_AD,'-') as data4
              from KIMLIK as kmlk
           inner join PERSONEL AS p
              on kmlk.KIMLIK_ID =p.KIMLIK_ID
           inner join (select fnKh.KIMLIK_ID, kig.GOREV_KURUM_ID, kig.GOREV_BIRIM_ID, kig.GOREV_UNVAN_ID, kig.GOREV_BRANS_ID, BIRIM.BIRIM_AD, BIRIM.BIRIM_ID, BIRIM.UST_BIRIM_ID
                           from KIMLIK_HAREKET as kh
                          inner join (select KIMLIK_ID, HID
                                  from fnTbl_KIMLIK_HAREKET('{start_date}', DATEADD(DAY,1,'{end_date}'), '2075-01-01')
                                 group by KIMLIK_ID, HID) as fnKh
                           on (fnKh.HID = kh.KIMLIK_HAREKET_ID)
                          inner join KIMLIK_IS_GECMISI as kig
                           on (isnull(kh.IS_GECMISI_ID, kh.UCRETSIZ_IZIN_ID) = kig.IS_GECMISI_ID)
                       left join BIRIM
                       on BIRIM.BIRIM_ID=kig.GOREV_KURUM_ID
                          where (isnull(kh.PSF_ID, 0) = 0)
                          and (isnull(kig.PSF_ID, 0) = 0)) AS g
              on kmlk.KIMLIK_ID=g.KIMLIK_ID
            left outer join BIRIM as kk
              on (p.KADRO_KURUM_ID = kk.BIRIM_ID)
            left outer join UNVAN as ku
              on (p.KADRO_UNVAN_ID = ku.UNVAN_ID)
            left outer join BIRIM as gk
              on (g.GOREV_KURUM_ID = gk.BIRIM_ID)
            left outer join UNVAN as gu
              on (g.GOREV_UNVAN_ID = gu.UNVAN_ID)
            left outer join PERSONEL_TUR as pt
              on (p.PERSONEL_TUR_ID = pt.PERSONEL_TUR_ID)
           where (isnull(p.PSF_ID, 0) = 0)
             and (isnull(kmlk.PSF_ID, 0) = 0)
           and (kk.IC_BIRIM = 1 or gk.IC_BIRIM = 1)
        ) as CALISMA  
        WHERE ({tur_filter} is null or CALISMA.data5 = {tur_filter})
        order by data1
        """
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        print(f"❌ Personel tür detay sorgu hatası: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_personel_hizmet_sinif_ozet(start_date, end_date):
    """Hizmet sınıfı bazlı sayıları getirir."""
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()
    
    try:
        sql = f"""
        SELECT data1, COUNT(1) AS data2 FROM  (
          select
            isnull(hzm.TUR_DEGER,'-' ) as data1
            from KIMLIK as kmlk
           inner join PERSONEL AS p
              on kmlk.KIMLIK_ID =p.KIMLIK_ID
           inner join (select fnKh.KIMLIK_ID, kig.GOREV_KURUM_ID, kig.GOREV_BIRIM_ID, kig.GOREV_UNVAN_ID, kig.GOREV_BRANS_ID, BIRIM.BIRIM_AD, BIRIM.BIRIM_ID, BIRIM.UST_BIRIM_ID
                           from KIMLIK_HAREKET as kh
                          inner join (select KIMLIK_ID, HID
                                  from fnTbl_KIMLIK_HAREKET('{start_date}', DATEADD(DAY,1,'{end_date}'), '2075-01-01')
                                 group by KIMLIK_ID, HID) as fnKh
                           on (fnKh.HID = kh.KIMLIK_HAREKET_ID)
                          inner join KIMLIK_IS_GECMISI as kig
                           on (isnull(kh.IS_GECMISI_ID, kh.UCRETSIZ_IZIN_ID) = kig.IS_GECMISI_ID)
                       left join BIRIM
                       on BIRIM.BIRIM_ID=kig.GOREV_KURUM_ID
                          where (isnull(kh.PSF_ID, 0) = 0)
                          and (isnull(kig.PSF_ID, 0) = 0)) AS g
              on kmlk.KIMLIK_ID=g.KIMLIK_ID
            left outer join BIRIM as kk
              on (p.KADRO_KURUM_ID = kk.BIRIM_ID)
            left outer join UNVAN as ku
              on (p.KADRO_UNVAN_ID = ku.UNVAN_ID)
            left outer join BIRIM as gk
              on (g.GOREV_KURUM_ID = gk.BIRIM_ID)
            left outer join UNVAN as gu
              on (g.GOREV_UNVAN_ID = gu.UNVAN_ID)
          left outer join TUR_DETAY as hzm
              on (p.HIZMET_SINIF_TUR_ID = hzm.TUR_DETAY_ID)
           where (isnull(p.PSF_ID, 0) = 0)
             and (isnull(kmlk.PSF_ID, 0) = 0)
           and (kk.IC_BIRIM = 1 or gk.IC_BIRIM = 1)
           ) AS CALISMA
           GROUP BY data1
        """
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        print(f"❌ Hizmet sınıfı özet sorgu hatası: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_personel_hizmet_sinif_detay(start_date, end_date, hizmet_sinif=None):
    """Hizmet sınıfı bazlı detay listesini getirir."""
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()
    
    try:
        hizmet_filter = f"'{hizmet_sinif}'" if hizmet_sinif else "NULL"
        
        sql = f"""
        select dataId, data1, data3, data4 FROM (
          select kmlk.KIMLIK_ID as dataId, kmlk.KIMLIK_AD + ' ' + kmlk.KIMLIK_SOYAD AS data1,
                 gk.BIRIM_AD  as data3, isnull(hzm.TUR_DEGER, '-') as data5,
                 isnull(gu.UNVAN_AD,'-') as data4
              from KIMLIK as kmlk
           inner join PERSONEL AS p
              on kmlk.KIMLIK_ID =p.KIMLIK_ID
           inner join (select fnKh.KIMLIK_ID, kig.GOREV_KURUM_ID, kig.GOREV_BIRIM_ID, kig.GOREV_UNVAN_ID, kig.GOREV_BRANS_ID, BIRIM.BIRIM_AD, BIRIM.BIRIM_ID, BIRIM.UST_BIRIM_ID
                           from KIMLIK_HAREKET as kh
                          inner join (select KIMLIK_ID, HID
                                  from fnTbl_KIMLIK_HAREKET('{start_date}', DATEADD(DAY,1,'{end_date}'), '2075-01-01')
                                 group by KIMLIK_ID, HID) as fnKh
                           on (fnKh.HID = kh.KIMLIK_HAREKET_ID)
                          inner join KIMLIK_IS_GECMISI as kig
                           on (isnull(kh.IS_GECMISI_ID, kh.UCRETSIZ_IZIN_ID) = kig.IS_GECMISI_ID)
                       left join BIRIM
                       on BIRIM.BIRIM_ID=kig.GOREV_KURUM_ID
                          where (isnull(kh.PSF_ID, 0) = 0)
                          and (isnull(kig.PSF_ID, 0) = 0)) AS g
              on kmlk.KIMLIK_ID=g.KIMLIK_ID
            left outer join BIRIM as kk
              on (p.KADRO_KURUM_ID = kk.BIRIM_ID)
            left outer join UNVAN as ku
              on (p.KADRO_UNVAN_ID = ku.UNVAN_ID)
            left outer join BIRIM as gk
              on (g.GOREV_KURUM_ID = gk.BIRIM_ID)
            left outer join UNVAN as gu
              on (g.GOREV_UNVAN_ID = gu.UNVAN_ID)
            left outer join TUR_DETAY as hzm
              on (p.HIZMET_SINIF_TUR_ID = hzm.TUR_DETAY_ID)
           where (isnull(p.PSF_ID, 0) = 0)
             and (isnull(kmlk.PSF_ID, 0) = 0)
           and (kk.IC_BIRIM = 1 or gk.IC_BIRIM = 1)
        ) as CALISMA  
        WHERE ({hizmet_filter} is null or CALISMA.data5 = {hizmet_filter})
        order by data1
        """
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        print(f"❌ Hizmet sınıfı detay sorgu hatası: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_personel_tam_liste(start_date, end_date):
    """Tüm personel bilgilerini (frontend'de filtreleme için) getiren ana liste."""
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()
    
    try:
        sql = f"""
        select dataId, data1, data3, data4, DURUM as calisma_durumu, kadro_unvan, personel_turu, hizmet_sinifi FROM (
          select kmlk.KIMLIK_ID as dataId, kmlk.KIMLIK_AD + ' ' + kmlk.KIMLIK_SOYAD AS data1,
                 gk.BIRIM_AD as data3,
                 isnull(gu.UNVAN_AD,ku.UNVAN_AD) as data4,
              CASE WHEN ISNULL(GK.IC_BIRIM,1) = 0 AND ISNULL(KK.IC_BIRIM,1) = 1 THEN 'GEÇİCİ GÖREVLİ GİDEN'
                  WHEN CALISMA.DURUM = 'RAPORLU' THEN 'RAPORLU' 
                WHEN CALISMA.DURUM = 'İZİNLİ' THEN 'İZİNLİ'
                ELSE 'ÇALIŞIYOR'
             END AS DURUM,
             isnull(ku.UNVAN_AD,'-') as kadro_unvan,
             isnull(pt.PERSONEL_TUR_AD, '-') as personel_turu,
             isnull(hzm.TUR_DEGER, '-') as hizmet_sinifi
            from KIMLIK as kmlk
           inner join PERSONEL AS p
              on kmlk.KIMLIK_ID =p.KIMLIK_ID
            left outer join ( select sum(CALISMA_GUN) as CALISMA_GUN, sum(UCRETSIZ_IZIN_GUN) as UCRETSIZ_IZIN_GUN, sum(IZIN_GUN) as IZIN_GUN, c.KIMLIK_ID, HID, 
                     case when td.TUR_DEGER_KOD = 'RAPORLUIZIN' OR td.TUR_DEGER_KOD = 'TEKTABIPRAPORU' OR td.TUR_DEGER_KOD = 'HEYETRAPORU' THEN 'RAPORLU'
                        when td.TUR_DEGER_KOD <> '' then 'İZİNLİ' ELSE null end as DURUM
                         from fnTbl_KIMLIK_HAREKET_CALISMA('{start_date}', '{end_date}', '2075-01-01') as c
                     left join KIMLIK_HAREKET as kh on kh.KIMLIK_HAREKET_ID = c.HID
                     left join IZIN as i on i.IZIN_ID = kh.IZIN_ID
                     left join TUR_DETAY as td on td.TUR_DETAY_ID = i.IZIN_TUR_ID
                        group by c.KIMLIK_ID, HID, IZIN_TUR_ID, td.TUR_DEGER_KOD) AS CALISMA
              on CALISMA.KIMLIK_ID = kmlk.KIMLIK_ID
           inner join KIMLIK_HAREKET as kh
              on kh.KIMLIK_ID=kmlk.KIMLIK_ID and CALISMA.HID=kh.KIMLIK_HAREKET_ID
            left outer join IZIN as i
            on i.IZIN_ID= kh.IZIN_ID
            left outer join TUR_DETAY as td
            on td.TUR_DETAY_ID=i.IZIN_TUR_ID
            left outer join (select fnKh.KIMLIK_ID, kig.GOREV_KURUM_ID, kig.GOREV_BIRIM_ID, kig.GOREV_UNVAN_ID, kig.GOREV_BRANS_ID, BIRIM.BIRIM_AD, BIRIM.BIRIM_ID, BIRIM.UST_BIRIM_ID
                           from KIMLIK_HAREKET as kh
                          inner join (select KIMLIK_ID, HID
                                  from fnTbl_KIMLIK_HAREKET('{start_date}', DATEADD(DAY,1,'{end_date}'), '2075-01-01')
                                 group by KIMLIK_ID, HID) as fnKh
                           on (fnKh.HID = kh.KIMLIK_HAREKET_ID)
                          inner join KIMLIK_IS_GECMISI as kig
                           on (isnull(kh.IS_GECMISI_ID, kh.UCRETSIZ_IZIN_ID) = kig.IS_GECMISI_ID)
                       left join BIRIM
                       on BIRIM.BIRIM_ID=kig.GOREV_KURUM_ID
                          where (isnull(kh.PSF_ID, 0) = 0)
                          and (isnull(kig.PSF_ID, 0) = 0)) AS g
              on kmlk.KIMLIK_ID=g.KIMLIK_ID
            left outer join BIRIM as kk
              on (p.KADRO_KURUM_ID = kk.BIRIM_ID)
            left outer join UNVAN as ku
              on (p.KADRO_UNVAN_ID = ku.UNVAN_ID)
            left outer join BIRIM as gk
              on (g.GOREV_KURUM_ID = gk.BIRIM_ID)
            left outer join UNVAN as gu
              on (g.GOREV_UNVAN_ID = gu.UNVAN_ID)
            left outer join PERSONEL_TUR as pt
              on (p.PERSONEL_TUR_ID = pt.PERSONEL_TUR_ID)
            left outer join TUR_DETAY as hzm
              on (p.HIZMET_SINIF_TUR_ID = hzm.TUR_DETAY_ID)
           where (isnull(p.PSF_ID, 0) = 0)
             and (isnull(kh.PSF_ID, 0) = 0)
             and (isnull(kk.PSF_ID, 0) = 0)
             and (isnull(gk.PSF_ID, 0) = 0)
             and (isnull(gu.PSF_ID, 0) = 0)
             and (isnull(ku.PSF_ID, 0) = 0)
             and (isnull(kmlk.PSF_ID, 0) = 0)
           and (kk.IC_BIRIM = 1 or gk.IC_BIRIM = 1)
             and (kk.BIRIM_OZELLIK is null or kk.BIRIM_OZELLIK & 1 = 1)
             and (gk.BIRIM_OZELLIK is null or gk.BIRIM_OZELLIK & 1 = 1)
        ) as CALISMA  
        order by data1
        """
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        print(f"❌ Personel tam liste sorgu hatası: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
