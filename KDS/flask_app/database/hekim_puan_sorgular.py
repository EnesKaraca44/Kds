import pandas as pd
from .baglanti import baglanti_olustur
from .cache_helper import ttl_cache
from .sql_api_client import get_remote_sql


def _fix_known_group_by_mismatch(sql: str) -> str:
    """
    HEKIM_PUAN_TAB1 bazı ortamlarda şu uyumsuzlukla geliyor:
    - SELECT: shh.PERFORMANS_TRH as islemTrh
    - GROUP BY: shh.ISLEM_TRH
    Bu durumda SQL Server 8120 hatası üretir.
    """
    if not isinstance(sql, str) or not sql:
        return sql

    if "shh.PERFORMANS_TRH as islemTrh" in sql and "shh.ISLEM_TRH" in sql:
        return sql.replace("shh.ISLEM_TRH", "shh.PERFORMANS_TRH")

    return sql


def _read_sql_with_optional_params(conn, sql, start_date, end_date):
    """
    API'den gelen SQL {start_date}/{end_date} veya @...@ ile dolu olabilir;
    bazen ODBC ? parametreleri kalir (eski sablon).
    """
    qmarks = sql.count("?")
    if qmarks == 0:
        return pd.read_sql(sql, conn)
    if qmarks == 2:
        return pd.read_sql(sql, conn, params=(start_date, end_date))
    if qmarks == 4:
        return pd.read_sql(sql, conn, params=(start_date, end_date, start_date, end_date))
    return pd.read_sql(sql, conn)


@ttl_cache(maxsize=32, ttl=600)
def hekim_puan_verisi_yukle(start_date, end_date):
    """Hekim hizmet puan detay verisi; SQL Rapor API'den (HEKIM_PUAN_TAB1) gelir."""
    conn = baglanti_olustur()
    if not conn:
        return None

    try:
        sql = get_remote_sql(
            "hekim_puan.hekim_puan_verisi_yukle",
            {"start_date": start_date, "end_date": end_date},
        )
        if not sql:
            return None

        sql = _fix_known_group_by_mismatch(sql)
        
        # Daha güvenli bir değişim için Regex (Büyük/Küçük harf duyarsız) kullanıyoruz
        import re
        # 1. Tarih konusunu düzeltiyoruz: 
        # Sorgudaki tüm tırnak içindeki tarihleri (YYYY-MM-DD, YYYY.MM.DD vb.) yakalıyoruz
        found_dates = re.findall(r"'\d{1,4}[./-]\d{1,2}[./-]\d{1,4}(?:\s\d{2}:\d{2}:\d{2})?'", sql)
        if len(found_dates) >= 2:
            sql = sql.replace(found_dates[0], f"'{start_date}'")
            for i in range(1, len(found_dates)):
                sql = sql.replace(found_dates[i], f"'{end_date}'")
        
        df = _read_sql_with_optional_params(conn, sql, start_date, end_date)
        
        with open(r"c:\Users\ENES\Desktop\KDS_enson\KDS\flask_app\debug_log.txt", "w", encoding="utf-8") as f:
            f.write("SQL BASARILI\n")
            f.write(f"SQL Uzunlugu: {len(sql)}\n")
            f.write(f"Donen Satir: {len(df) if df is not None else 0}\n")
            f.write(f"SQL:\n{sql}\n")

        return df
    except Exception as e:
        with open(r"c:\Users\ENES\Desktop\KDS_enson\KDS\flask_app\debug_log.txt", "w", encoding="utf-8") as f:
            f.write(f"SQL HATASI: {str(e)}\n\n")
            import traceback
            f.write(traceback.format_exc())
            try:
                f.write(f"\n\nSQL:\n{sql}\n")
            except:
                pass
        print(f"Hekim Puan Verisi Yükleme Hatasi: {e}")
        return None
    finally:
        conn.close()
