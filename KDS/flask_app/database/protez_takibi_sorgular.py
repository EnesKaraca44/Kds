import pandas as pd
from .baglanti import baglanti_olustur
from .cache_helper import ttl_cache
from .sql_api_client import get_remote_sql


@ttl_cache(maxsize=32, ttl=600)
def asama_girilmemis_hasta_listesi_yukle(hizmet_sut_kodu=None, islem_tarihi=None, birim_id=None):
    """
    Asama girilmemis hasta listesini getirir.
    - hizmet_sut_kodu: ilgili SUT kodu (opsiyonel)
    - islem_tarihi: YYYY-MM-DD formatinda tarih (opsiyonel)
    - birim_id: servis birim id (opsiyonel)
    """
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    try:
        sql = get_remote_sql(
            "protez_takibi.asama_girilmemis_hasta_listesi_yukle",
            {
                "SUT_KODU": hizmet_sut_kodu or "",
                "ISLEM_TARIHI": islem_tarihi or "",
                "BIRIM_ID": birim_id or "",
            },
        )
        if not sql:
            return pd.DataFrame()
        return pd.read_sql(sql, conn)
    except Exception as e:
        print(f"❌ Asama girilmemis hasta listesi hatasi: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


@ttl_cache(maxsize=32, ttl=600)
def protez_suresi_gecen_hasta_birim_yukle(birim_id_csv=None):
    """
    Protez suresi gecen hasta/birim listesini getirir.
    - birim_id_csv: '12,13,14' gibi CSV birim id listesi (opsiyonel)
    """
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    try:
        sql = get_remote_sql(
            "protez_takibi.protez_suresi_gecen_hasta_birim_yukle",
            {"BIRIM_ID": birim_id_csv or ""},
        )
        if not sql:
            return pd.DataFrame()
        return pd.read_sql(sql, conn)
    except Exception as e:
        print(f"❌ Protez suresi gecen hasta/birim hatasi: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
