import pandas as pd
import os
import re
from .baglanti import baglanti_olustur
from .cache_helper import ttl_cache
from .sql_api_client import get_remote_sql


_APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_DEBUG_LOG_FILE = os.path.join(_APP_ROOT, "debug_log.txt")


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


def _fix_outer_where_one_day_filter(sql, start_date, end_date) -> str:
    """
    HEKIM_PUAN_TAB1 şablonunun dış WHERE klozu yanlış parametre kullanıyor:
        AND (islemTrh >= '@BASLANGIC_TRH@') AND (islemTrh < DATEADD(day, 1, '@BASLANGIC_TRH@'))
    İki sınır da başlangıç tarihiyle çalıştığı için sorgu seçilen aralıktan bağımsız
    olarak hep tek günlük (yalnızca başlangıç gününe ait) sonuç döner.
    Bu fonksiyon, substitution sonrası SQL'de bu kalıbı bulup üst sınırdaki tarihi
    end_date ile düzeltir.
    """
    if not isinstance(sql, str) or not sql or not start_date or not end_date:
        return sql

    sd = str(start_date)
    ed = str(end_date)
    if sd == ed:
        return sql

    pattern = re.compile(
        r"(\(\s*islemTrh\s*>=\s*'"
        + re.escape(sd)
        + r"'\s*\)\s*AND\s*\(\s*islemTrh\s*<\s*DATEADD\s*\(\s*day\s*,\s*1\s*,\s*')"
        + re.escape(sd)
        + r"('\s*\)\s*\))",
        re.IGNORECASE,
    )
    return pattern.sub(lambda m: m.group(1) + ed + m.group(2), sql)


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


@ttl_cache(maxsize=32, ttl=60)
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
        sql = _fix_outer_where_one_day_filter(sql, start_date, end_date)

        df = _read_sql_with_optional_params(conn, sql, start_date, end_date)
        
        with open(_DEBUG_LOG_FILE, "w", encoding="utf-8") as f:
            f.write("SQL BASARILI\n")
            f.write(f"SQL Uzunlugu: {len(sql)}\n")
            f.write(f"Donen Satir: {len(df) if df is not None else 0}\n")
            f.write(f"SQL:\n{sql}\n")

        return df
    except Exception as e:
        with open(_DEBUG_LOG_FILE, "w", encoding="utf-8") as f:
            f.write(f"SQL HATASI: {str(e)}\n\n")
            import traceback
            f.write(traceback.format_exc())
            try:
                f.write(f"\n\nSQL:\n{sql}\n")
            except Exception:
                pass
        print(f"Hekim Puan Verisi Yükleme Hatasi: {e}")
        return None
    finally:
        conn.close()
