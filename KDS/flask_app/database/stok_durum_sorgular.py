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
            # birimAd = is yeri adi (BIRIM_AD); olcu birimi degil
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

    if out.columns.duplicated().any():
        out = out.loc[:, ~out.columns.duplicated(keep="first")]

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


def _detay_satir_tipi(hareket_tip, envanter_tip, belge_ad) -> str:
    """
    Alis/satis/diger ayrimi:
    1) stokHareketTip kodu (HAREKETSATINALMA / HAREKETSATIS) en guvenilir.
    2) hareketEnvanterTip (1=giris->alis, 2=cikis->satis).
    3) Son care: belge adindan kelime eslesmesi.
    """
    kod = str(hareket_tip or "").strip().upper()
    if "SATINALMA" in kod or "ECZANE" in kod or "GIRIS" in kod:
        return "alis"
    if "SATIS" in kod or "CIKIS" in kod:
        return "satis"

    try:
        et = int(float(envanter_tip))
    except (TypeError, ValueError):
        et = 0
    if et == 1:
        return "alis"
    if et == 2:
        return "satis"

    low = str(belge_ad or "").lower()
    if "satinal" in low or "sat\u0131nal" in low or "al\u0131\u015f" in low or "alis" in low or "giri\u015f" in low or "giris" in low:
        return "alis"
    if "sat\u0131\u015f" in low or "satis" in low or "\u00e7\u0131k\u0131\u015f" in low or "cikis" in low:
        return "satis"
    return "diger"


def _detay_num(val) -> float:
    num = pd.to_numeric(val, errors="coerce")
    return float(num) if pd.notna(num) else 0.0


def _detay_satis_birim_fiyat(miktar, net_satis, cikis_mlyt, fallback_fiyat=0.0):
    """
    Satış birim fiyatı ve kaynağı.
    net_satis / cikis_mlyt yoksa None döner (shFiyat ile aynı göstermeyelim).
    """
    miktar = _detay_num(miktar)
    net_satis = _detay_num(net_satis)
    cikis_mlyt = _detay_num(cikis_mlyt)
    if miktar > 0 and net_satis > 0:
        return net_satis / miktar, "net_satis"
    if miktar > 0 and cikis_mlyt > 0:
        return cikis_mlyt / miktar, "cikis_mlyt"
    fb = _detay_num(fallback_fiyat)
    if fb > 0:
        return fb, "sh_fiyat_yedek"
    return None, "yok"


def _detay_tarih(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    if hasattr(val, "strftime"):
        try:
            return val.strftime("%d.%m.%Y")
        except (ValueError, OSError):
            return ""
    return str(val).strip()


def _fix_stok_alis_satis_sql(sql: str) -> str:
    """Rapor API'ye kaydedilen detay SQL'ini calistirilabilir forma getirir."""
    if not isinstance(sql, str) or not sql.strip():
        return sql

    fixed = sql.strip().rstrip(";").strip()
    if fixed.startswith("(") and fixed.endswith(")") and fixed[1:].lstrip().lower().startswith("select"):
        fixed = fixed[1:-1].strip()
    return fixed


@ttl_cache(maxsize=128, ttl=60)
def stok_durum_detay_yukle(stok_kart_id, start_date_str, end_date_str, butce_tur_id=831):
    """Tek bir stok kartinin hareket detayini doner: ozet + satirlar."""
    bos = {"ozet": {}, "satirlar": [], "count": 0}

    try:
        sid = int(float(str(stok_kart_id).strip()))
    except (TypeError, ValueError):
        return bos
    if sid <= 0:
        return bos

    try:
        butce = int(butce_tur_id)
    except (TypeError, ValueError):
        butce = 0

    conn = baglanti_olustur()
    if not conn:
        return bos

    try:
        sql = get_remote_sql(
            "stok_durum.stok_durum_detay_yukle",
            {
                "start_date": start_date_str,
                "end_date": end_date_str,
                "TARIH1": start_date_str,
                "TARIH2": end_date_str,
                "butce": butce,
                "BUTCE": butce,
                "stok_id": sid,
                "STOK_ID": sid,
                "BIRIM_ID": "",
            },
        )
        if not sql:
            print("[STOK_DURUM_DETAY] stok_durum.stok_durum_detay_yukle -> STOK_ALIS_SATIS SQL metni alinamadi")
            return bos

        sql = _fix_stok_alis_satis_sql(sql)
        df = pd.read_sql(sql, conn)
        df = _normalize_stok_durum_columns(df)

        print(f"[STOK_DURUM_DETAY] stok_id={sid} rows={len(df)}")
        if df is not None and not df.empty:
            tipler = df["stokHareketTip"].dropna().unique().tolist() if "stokHareketTip" in df.columns else "-"
            envanter = df["hareketEnvanterTip"].dropna().unique().tolist() if "hareketEnvanterTip" in df.columns else "-"
            print(f"[STOK_DURUM_DETAY] stokHareketTip={tipler} hareketEnvanterTip={envanter}")

        if df is None or df.empty:
            return bos

        # SQL rowNumber = sfTarih asc (en eski once). Once eski->yeni siralayalim
        # ki son alis/satis dogru hesaplansin, sonra gosterim icin ters cevirelim.
        if "RowNumber" in df.columns:
            df = (
                df.assign(_rn=pd.to_numeric(df["RowNumber"], errors="coerce"))
                .sort_values("_rn", kind="stable")
                .drop(columns="_rn")
            )

        satirlar = []
        for _, row in df.iterrows():
            belge = str(row.get("belgeAd") or "").strip()
            miktar = _detay_num(row.get("shMiktar"))
            fiyat = _detay_num(row.get("shFiyat"))
            net_satis = _detay_num(row.get("shNetSatisTutar"))
            cikis_mlyt = _detay_num(row.get("shCikisMlytTutar"))
            tip = _detay_satir_tipi(
                row.get("stokHareketTip"),
                row.get("hareketEnvanterTip"),
                belge,
            )
            satis_birim, satis_kaynak = _detay_satis_birim_fiyat(miktar, net_satis, cikis_mlyt, fiyat)
            if tip == "satis" and satis_birim is not None:
                birim_fiyat = satis_birim
            else:
                birim_fiyat = fiyat
            satirlar.append(
                {
                    "tarih": _detay_tarih(row.get("sfTarih")) or _detay_tarih(row.get("shTarih")),
                    "belge": belge,
                    "tip": tip,
                    "cari": str(row.get("cariKartAdi") or "").strip(),
                    "birim": str(row.get("shOlcuBirimAd") or "").strip(),
                    "miktar": miktar,
                    "fiyat": fiyat,
                    "satis_birim_fiyat": satis_birim,
                    "satis_fiyat_kaynak": satis_kaynak,
                    "birim_fiyat": birim_fiyat,
                    "kdvsiz_fiyat": _detay_num(row.get("kdvsizShFiyat")),
                    "kdv_oran": _detay_num(row.get("shKdvOran")),
                    "toplam": _detay_num(row.get("shToplam")),
                    "net_tutar": _detay_num(row.get("shKdvNetTutar")),
                    "net_satis_tutar": net_satis,
                    "cikis_mlyt_tutar": cikis_mlyt,
                    "belge_no": str(row.get("sfBelgeNo") or row.get("sfFaturaNo") or "").strip(),
                }
            )

        son_alis = next((s for s in reversed(satirlar) if s["tip"] == "alis"), None)
        son_satis = next((s for s in reversed(satirlar) if s["tip"] == "satis"), None)
        if son_satis:
            print(
                f"[STOK_DURUM_DETAY] son satis ornek stok_id={sid}: "
                f"shFiyat={son_satis.get('fiyat')} "
                f"netSatis={son_satis.get('net_satis_tutar')} "
                f"cikisMlyt={son_satis.get('cikis_mlyt_tutar')} "
                f"hesaplanan={son_satis.get('satis_birim_fiyat')} "
                f"kaynak={son_satis.get('satis_fiyat_kaynak')}"
            )
        if son_alis:
            print(
                f"[STOK_DURUM_DETAY] son alis ornek stok_id={sid}: "
                f"shFiyat={son_alis.get('fiyat')} toplam={son_alis.get('toplam')}"
            )
        ilk = df.iloc[0]

        # Gosterimde en son islem en ustte olsun (yeni -> eski).
        satirlar.reverse()

        ozet = {
            "stok_kod": str(ilk.get("stokKod") or "").strip(),
            "stok_ad": str(ilk.get("stokAd") or "").strip(),
            "birim": str(ilk.get("shOlcuBirimAd") or "").strip(),
            "toplam_hareket": len(satirlar),
            "son_alis_fiyat": son_alis["fiyat"] if son_alis else None,
            "son_alis_tarih": son_alis["tarih"] if son_alis else "",
            "son_alis_cari": son_alis["cari"] if son_alis else "",
            "son_satis_fiyat": son_satis["satis_birim_fiyat"] if son_satis else None,
            "son_satis_tarih": son_satis["tarih"] if son_satis else "",
            "son_satis_kaynak": son_satis.get("satis_fiyat_kaynak", "") if son_satis else "",
        }

        return {"ozet": ozet, "satirlar": satirlar, "count": len(satirlar)}
    except Exception as e:
        print(f"Stok durum detay yukleme hatasi: {e}")
        return bos
    finally:
        conn.close()
