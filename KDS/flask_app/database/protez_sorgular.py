import warnings

import pandas as pd
from datetime import datetime

from .baglanti import baglanti_olustur
from .cache_helper import ttl_cache
from .sql_api_client import get_remote_sql


def _normalize_broken_null_literals(sql: str) -> str:
    if not isinstance(sql, str) or not sql:
        return sql
    normalized = sql.replace("'NULL'", "NULL")
    normalized = normalized.replace("'null'", "NULL")
    return normalized


def _read_sql_pd(conn, sql, params=None):
    """pyodbc + pandas UserWarning (SQLAlchemy onerisi) gurultusunu bastirir."""
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="pandas only supports SQLAlchemy connectable",
            category=UserWarning,
        )
        if params is not None:
            return pd.read_sql(sql, conn, params=params)
        return pd.read_sql(sql, conn)


@ttl_cache(maxsize=32, ttl=60)
def protez_verisi_yukle(start_date, end_date):
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    start_dt = pd.to_datetime(start_date).strftime("%Y-%m-%d")
    end_dt = pd.to_datetime(end_date).strftime("%Y-%m-%d")

    try:
        sql = get_remote_sql(
            "protez.protez_verisi_yukle",
            {"start_date": start_dt, "end_date": end_dt},
        )
        if not sql:
            print("[PROTEZ] get_remote_sql bos dondu (API kodu veya SQL metni yok).")
            return pd.DataFrame()
        sql = _normalize_broken_null_literals(sql)

        if "?" in sql:
            start_param = datetime.strptime(f"{start_dt} 00:00:00", "%Y-%m-%d %H:%M:%S")
            end_param = datetime.strptime(f"{end_dt} 00:00:00", "%Y-%m-%d %H:%M:%S")
            qmarks = sql.count("?")
            if qmarks == 1:
                df = _read_sql_pd(conn, sql, params=[start_param])
            elif qmarks == 2:
                df = _read_sql_pd(conn, sql, params=[start_param, end_param])
            else:
                # Cogu rapor: baslangic, bitis tekrari (?, ?, ?, ?) veya fazladan ODBC parametresi
                seq = []
                for i in range(qmarks):
                    seq.append(start_param if i % 2 == 0 else end_param)
                df = _read_sql_pd(conn, sql, params=seq)
        else:
            df = _read_sql_pd(conn, sql)

        if df is None or df.empty:
            print(
                f"[PROTEZ] Sorgu satir dondurmedi ({start_dt} .. {end_dt}), "
                f"kolon sayisi={0 if df is None else len(df.columns)}"
            )
            return pd.DataFrame()

        df.columns = [
            str(c)
            .replace(" ", "_")
            .replace("ı", "i")
            .replace("İ", "I")
            .upper()
            for c in df.columns
        ]

        numeric_cols = [
            "PLANLANANTESLIMSURESI",
            "PLAN_SURE",
            "HEDEF_GUN",
            "ORTALAMA_TESLIM_SURESI",
            "TESLIM_SURE_GUN",
            "GERCEK_SURE",
            "PROTEZTESLIMSURE",
            "TARIHFARK",
            "HASTASAYISI",
            "HIZMETSAYISI",
        ]
        # SURE: SQL'de 0-3 trafik isigi (CASE); sayisal tutulabilir ama gecikme hesabinda kullanilmaz

        for col in numeric_cols:
            if col in df.columns:
                if df[col].dtype == "object":
                    df[col] = df[col].astype(str).str.replace(",", ".")
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
                df[col] = df[col].round(1)

        return df

    except Exception as e:
        print(f"Protez verisi (API) yuklenirken hata: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
