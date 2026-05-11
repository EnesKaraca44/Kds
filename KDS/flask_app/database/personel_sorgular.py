import pandas as pd
from .baglanti import baglanti_olustur
from .sql_api_client import get_remote_sql

# Personel Sorgulama ile ilgili SQL sorguları bu dosyada toplanacaktır.

def get_personel_calisma_durumu_ozet(start_date, end_date):
    """Personel çalışma durumu özet verilerini (sayıları) getirir."""
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()
    
    try:
        sql = get_remote_sql(
            "personel.get_personel_calisma_durumu_ozet",
            {"start_date": start_date, "end_date": end_date},
        )
        if not sql:
            return pd.DataFrame()
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        print(f"Personel ozet sorgu hatasi: {e}")
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
        sql = get_remote_sql(
            "personel.get_personel_calisma_durumu_detay",
            {
                "start_date": start_date,
                "end_date": end_date,
                "calisma_tur_filter": calisma_tur_filter,
            },
        )
        if not sql:
            return pd.DataFrame()
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        print(f"Personel detay sorgu hatasi: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_personel_kadro_unvan_ozet(start_date, end_date):
    """Kadro unvanı bazlı personel sayılarını getirir."""
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()
    
    try:
        sql = get_remote_sql(
            "personel.get_personel_kadro_unvan_ozet",
            {"start_date": start_date, "end_date": end_date},
        )
        if not sql:
            return pd.DataFrame()
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        print(f"Kadro unvan ozet sorgu hatasi: {e}")
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
        sql = get_remote_sql(
            "personel.get_personel_kadro_unvan_detay",
            {
                "start_date": start_date,
                "end_date": end_date,
                "kadro_filter": kadro_filter,
            },
        )
        if not sql:
            return pd.DataFrame()
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        print(f"Kadro unvan detay sorgu hatasi: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_personel_tur_ozet(start_date, end_date):
    """Personel türü bazlı sayıları getirir."""
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()
    
    try:
        sql = get_remote_sql(
            "personel.get_personel_tur_ozet",
            {"start_date": start_date, "end_date": end_date},
        )
        if not sql:
            return pd.DataFrame()
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        print(f"Personel tur ozet sorgu hatasi: {e}")
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
        sql = get_remote_sql(
            "personel.get_personel_tur_detay",
            {
                "start_date": start_date,
                "end_date": end_date,
                "tur_filter": tur_filter,
            },
        )
        if not sql:
            return pd.DataFrame()
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        print(f"Personel tur detay sorgu hatasi: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_personel_hizmet_sinif_ozet(start_date, end_date):
    """Hizmet sınıfı bazlı sayıları getirir."""
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()
    
    try:
        sql = get_remote_sql(
            "personel.get_personel_hizmet_sinif_ozet",
            {"start_date": start_date, "end_date": end_date},
        )
        if not sql:
            return pd.DataFrame()
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        print(f"Hizmet sinifi ozet sorgu hatasi: {e}")
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
        sql = get_remote_sql(
            "personel.get_personel_hizmet_sinif_detay",
            {
                "start_date": start_date,
                "end_date": end_date,
                "hizmet_filter": hizmet_filter,
            },
        )
        if not sql:
            return pd.DataFrame()
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        print(f"Hizmet sinifi detay sorgu hatasi: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_personel_tam_liste(start_date, end_date):
    """Tüm personel bilgilerini (frontend'de filtreleme için) getiren ana liste."""
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()
    
    try:
        sql = get_remote_sql(
            "personel.get_personel_tam_liste",
            {"start_date": start_date, "end_date": end_date},
        )
        if not sql:
            return pd.DataFrame()
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        print(f"Personel tam liste sorgu hatasi: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
