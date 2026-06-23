import pandas as pd
import re
from datetime import datetime

from .baglanti import baglanti_olustur
from .cache_helper import ttl_cache
from .malzeme_sorgular import _parse_miad_dates, _safe_read_sql
from .sql_api_client import get_remote_sql


def _fix_stok_durum_sql(sql: str) -> str:
    """
    STOK_DURUM rapor SQL'inde bilinen yazim hatalarini duzeltir.
    Kalici cozum: Rapor API'deki STOK_DURUM sablonunu guncellemek.
    """
    if not isinstance(sql, str) or not sql:
        return sql

    fixed = sql
    # STOK_SEVIYE_JENERIK tablosunda SH_BIRIM_ID yok; dogru kolon BIRIM_ID
    fixed = re.sub(r"\bsvj\.SH_BIRIM_ID\b", "svj.BIRIM_ID", fixed, flags=re.IGNORECASE)
    # JOIN alias tutarsizligi: LEFT JOIN ... sfis ... ama SELECT'te sFis
    fixed = re.sub(r"\bsFis\.", "sfis.", fixed)
    # GROUP BY icinde sh. oneki eksik kolonlar
    fixed = re.sub(
        r"(\bsh\.SH_BATCH_NO,\s*)SH_DOVIZ_KUR,\s*SH_DOVIZ_TOPLAM,\s*SH_DOVIZ_TUR_ID,\s*SH_FIYAT_DVZ",
        r"\1sh.SH_DOVIZ_KUR, sh.SH_DOVIZ_TOPLAM, sh.SH_DOVIZ_TUR_ID, sh.SH_FIYAT_DVZ",
        fixed,
        flags=re.IGNORECASE,
    )
    return fixed


def _normalize_stok_durum_columns(df: pd.DataFrame) -> pd.DataFrame:
    """API/SQL Server kolon adlarini tek forma getirir."""
    if df is None or df.empty:
        return df

    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]

    rename = {}
    for col in list(out.columns):
        key = col.replace(" ", "").lower()
        canonical = {
            "rownumber": "RowNumber",
            "hareketturbelgead": "hareketTurBelgeAd",
            "hareket_tur_belge_ad": "hareketTurBelgeAd",
            "belgead": "hareketTurBelgeAd",
            "hareket_tur_ad": "hareketTurBelgeAd",
            "shstokkod": "shStokKod",
            "stokkodu": "shStokKod",
            "stok_kodu": "shStokKod",
            "shstokad": "shStokAd",
            "stokad": "shStokAd",
            "stok_ad": "shStokAd",
            "shstokaciklama": "shStokAciklama",
            "stokaciklama": "shStokAciklama",
            "sholcubirimad": "shOlcuBirimAd",
            "olcubirimad": "shOlcuBirimAd",
            "birimad": "shOlcuBirimAd",
            "shmiktar": "shMiktar",
            "girismiktari": "shMiktar",
            "shcikismiktar": "shCikisMiktar",
            "cikismiktari": "shCikisMiktar",
            "shmevcutmiktar": "shMevcutMiktar",
            "mevcutmiktar": "shMevcutMiktar",
            "kritikstokmiktar": "kritikStokMiktar",
            "kritikmiktar": "kritikStokMiktar",
            "minstokmiktar": "minStokMiktar",
            "minimummiktar": "minStokMiktar",
            "maxstokmiktar": "maxStokMiktar",
            "maximummiktar": "maxStokMiktar",
            "yillikstokmiktar": "yillikStokMiktar",
            "yillikmiktar": "yillikStokMiktar",
            "shvadetarih": "shVadeTarih",
            "sonkullanimtarihi": "shVadeTarih",
            "shserilotnumber": "shSeriLotNumber",
            "serilotnumber": "shSeriLotNumber",
            "serilotnumarasi": "shSeriLotNumber",
            "shkunyno": "shKunyeNo",
            "kunyno": "shKunyeNo",
            "shbatchno": "shBatchNo",
            "batchno": "shBatchNo",
        }.get(key)
        if canonical and col != canonical:
            rename[col] = canonical

    if rename:
        out = out.rename(columns=rename)
    return out


@ttl_cache(maxsize=32, ttl=60)
def stok_durum_verisi_yukle(start_date_str, end_date_str, birim_id=None, birim_id_list=None):
    """Stok durum listesi — Rapor API (STOK_DURUM)."""
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    if birim_id:
        birim_id_param = str(int(birim_id))
    elif birim_id_list:
        birim_id_param = ",".join(str(int(x)) for x in birim_id_list)
    else:
        birim_id_param = ""

    try:
        sql = get_remote_sql(
            "stok_durum.stok_durum_verisi_yukle",
            {
                "start_date": start_date_str,
                "end_date": end_date_str,
                "BIRIM_ID": birim_id_param,
                "TARIH": end_date_str,
            },
        )
        if not sql:
            return pd.DataFrame()

        sql = _fix_stok_durum_sql(sql)

        start_dt = datetime.strptime(f"{start_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(f"{end_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")

        df = _safe_read_sql(
            conn,
            sql,
            [
                (start_dt, end_dt, birim_id_param),
                (start_date_str, end_date_str, birim_id_param),
                (start_dt, end_dt, birim_id_param, birim_id_param),
                (start_date_str, end_date_str, birim_id_param, birim_id_param),
                (start_dt, end_dt),
                (start_date_str, end_date_str),
                (birim_id_param,),
            ],
        )

        df = _normalize_stok_durum_columns(df)

        if not df.empty:
            print(f"[STOK_DURUM] rows={len(df)} cols={list(df.columns)}")
            if "shStokAd" not in df.columns:
                sample = df.iloc[0].to_dict()
                print(f"[STOK_DURUM] UYARI: shStokAd yok — ilk satir ornegi: {sample}")

        if not df.empty and "shVadeTarih" in df.columns:
            df["shVadeTarih"] = _parse_miad_dates(df["shVadeTarih"])

        for col in (
            "shMiktar",
            "shCikisMiktar",
            "shMevcutMiktar",
            "kritikStokMiktar",
            "minStokMiktar",
            "maxStokMiktar",
            "yillikStokMiktar",
        ):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        return df
    except Exception as e:
        print(f"Stok durum veri yukleme hatasi: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
