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
            {
                "start_date": start_date,
                "end_date": end_date,
                # API SQL tarafinda farkli placeholder adlari kullanilabiliyor.
                "basTrh": start_date,
                "bitTrh": end_date,
                "BAS_TRH": start_date,
                "BIT_TRH": end_date,
            },
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
        calisma_tur_filter = str(calisma_tur).strip() if calisma_tur is not None and str(calisma_tur).strip() else None
        sql = get_remote_sql(
            "personel.get_personel_calisma_durumu_detay",
            {
                "start_date": start_date,
                "end_date": end_date,
                "calisma_tur_filter": calisma_tur_filter,
                "CALISMA_TUR_FILTER": calisma_tur_filter,
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

def get_personel_kadro_unvan_ozet(start_date, end_date, kadro_unvan=None):
    """Kadro unvanı bazlı personel sayılarını getirir."""
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()
    
    try:
        kadro_unvan_param = str(kadro_unvan).strip() if kadro_unvan is not None and str(kadro_unvan).strip() else None
        sql = get_remote_sql(
            "personel.get_personel_kadro_unvan_ozet",
            {
                "start_date": start_date,
                "end_date": end_date,
                "BASLANGIC_TRH": start_date,
                "BITIS_TRH": end_date,
                "KADRO_UNVAN": kadro_unvan_param,
                "kadro_unvan": kadro_unvan_param,
            },
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
        kadro_filter = str(kadro_unvan).strip() if kadro_unvan is not None and str(kadro_unvan).strip() else None
        sql = get_remote_sql(
            "personel.get_personel_kadro_unvan_detay",
            {
                "start_date": start_date,
                "end_date": end_date,
                "kadro_filter": kadro_filter,
                "BASLANGIC_TRH": start_date,
                "BITIS_TRH": end_date,
                "KADRO_UNVAN": kadro_filter,
                "kadro_unvan": kadro_filter,
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
            {
                "start_date": start_date,
                "end_date": end_date,
                "BASLANGIC_TRH": start_date,
                "BITIS_TRH": end_date,
                "baslangic_trh": start_date,
                "bitis_trh": end_date,
            },
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
        tur_filter = str(personel_tur).strip() if personel_tur is not None and str(personel_tur).strip() else None
        sql = get_remote_sql(
            "personel.get_personel_tur_detay",
            {
                "start_date": start_date,
                "end_date": end_date,
                "tur_filter": tur_filter,
                "BASLANGIC_TRH": start_date,
                "BITIS_TRH": end_date,
                "PERSONEL_TUR": tur_filter,
                "personel_tur": tur_filter,
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
            {
                "start_date": start_date,
                "end_date": end_date,
                "BASLANGIC_TRH": start_date,
                "BITIS_TRH": end_date,
                "baslangic_trh": start_date,
                "bitis_trh": end_date,
            },
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
        hizmet_filter = str(hizmet_sinif).strip() if hizmet_sinif is not None and str(hizmet_sinif).strip() else None
        sql = get_remote_sql(
            "personel.get_personel_hizmet_sinif_detay",
            {
                "start_date": start_date,
                "end_date": end_date,
                "hizmet_filter": hizmet_filter,
                "BASLANGIC_TRH": start_date,
                "BITIS_TRH": end_date,
                "HIZMET_SINIF": hizmet_filter,
                "hizmet_sinif": hizmet_filter,
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
            {
                "start_date": start_date,
                "end_date": end_date,
                "BASLANGIC_TRH": start_date,
                "BITIS_TRH": end_date,
                "baslangic_trh": start_date,
                "bitis_trh": end_date,
            },
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
