import pandas as pd
from .baglanti import baglanti_olustur
from .cache_helper import ttl_cache
from .sql_api_client import get_remote_sql


def _normalize_broken_null_literals(sql: str) -> str:
    if not isinstance(sql, str) or not sql:
        return sql
    return sql.replace("'NULL'", "NULL").replace("'null'", "NULL")


@ttl_cache(maxsize=32, ttl=600)
def rontgen_verisi_hekim(start_date_str, end_date_str):
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    try:
        sql = get_remote_sql(
            "rontgen.rontgen_verisi_hekim",
            {"start_date": start_date_str, "end_date": end_date_str},
        )
        if not sql:
            return pd.DataFrame()

        sql = _normalize_broken_null_literals(sql)
        df = pd.read_sql(sql, conn).copy()
        return df
    except Exception as e:
        print(f"❌ Radyoloji sorgu hatası: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


@ttl_cache(maxsize=32, ttl=600)
def rontgen_brans_verisi(start_date_str, end_date_str):
    """Branş bazlı röntgen tetkik dağılımını döndürür."""
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    try:
        sql = get_remote_sql(
            "rontgen.rontgen_brans_verisi",
            {"start_date": start_date_str, "end_date": end_date_str},
        )
        if not sql:
            return pd.DataFrame()

        sql = _normalize_broken_null_literals(sql)
        df = pd.read_sql(sql, conn).copy()
        return df
    except Exception as e:
        print(f"❌ Branş bazlı röntgen sorgu hatası: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
