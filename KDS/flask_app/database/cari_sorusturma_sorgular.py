import warnings
from datetime import datetime
import re

import pandas as pd

from .baglanti import baglanti_olustur
from .cache_helper import ttl_cache
from .sql_api_client import get_remote_sql

# Rapor API kodlari (rapor_sql_kod_map.json):
#   cari_sorusturma.cari_firma_ara         -> CARI_FIRMA_ARAMA
#   cari_sorusturma.cari_hareketleri_yukle -> CARI_FIRMA_SORUSTURMA
#   cari_sorusturma.banka_cari_fis           -> BANKA_CARI_FIS
#   cari_sorusturma.banka_cari_fis_hareket   -> BANKA_CARIF_FIS_HAREKET
#   cari_sorusturma.cari_finans               -> CARI_FINANS
#   cari_sorusturma.cari_finans_detay         -> CARI_FINANS_DETAY
#   cari_sorusturma.kasa_cari_fis             -> KASA_CARI_FIS
#   cari_sorusturma.alis_faturasi_master      -> ALIS_FATURASI_MASTER
#   cari_sorusturma.alis_faturasi_detay       -> ALIS_FATURASI_DETAY
#
# SQL metni Rapor API'den gelir; sorgu ana DATABASE baglantisi uzerinde calisir
# (diger sayfalarla ayni: ayarlar.py -> baglanti.py).


def _col_key(name):
    return str(name or "").strip().lower().replace(" ", "_")


# CARI_FIRMA_ARAMA cikti kolonlari -> UI alanlari
_CARI_LISTE_COL_KEYS = {
    "carikartid": "id",
    "cari_kart_id": "id",
    "cariid": "id",
    "id": "id",
    "carikartkodu": "kod",
    "cari_kart_kodu": "kod",
    "carikod": "kod",
    "cari_kod": "kod",
    "kod": "kod",
    "carikartadi": "unvan",
    "cari_kart_adi": "unvan",
    "cariunvan": "unvan",
    "unvan": "unvan",
}

# CARI_FIRMA_SORUSTURMA cikti kolonlari -> UI alanlari
_HAREKET_COL_KEYS = {
    # Modül
    "modulad": "modul",
    "modul": "modul",
    # Tarih
    "detaytarih": "tarih",
    "tarih": "tarih",
    # Fatura No
    "detayfaturano": "fatura_no",
    "faturano": "fatura_no",
    "fatura_no": "fatura_no",
    # Belge No
    "detaybelgeno": "belge_no",
    "belgeno": "belge_no",
    "belge_no": "belge_no",
    # Belge Tarihi
    "detaybelgetarih": "belge_tarihi",
    "belgetarihi": "belge_tarihi",
    "belge_tarihi": "belge_tarihi",
    # Vade / Valör Tarihi
    "detayvalortarih": "vade_tarihi",
    "vadetarihi": "vade_tarihi",
    "vade_tarihi": "vade_tarihi",
    # Açıklama
    "detayaciklama": "aciklama",
    "aciklama": "aciklama",
    # İşlem Türü (hareket tür adı)
    "detayhareketturad": "islem_turu",
    "islemturu": "islem_turu",
    "islem_turu": "islem_turu",
    # B/A (0/1)
    "detayba": "ba",
    "ba": "ba",
    # Tutar
    "detaytutar": "tutar",
    "tutar": "tutar",
    # Bakiye (yürüyen toplam, sayısal)
    "detaybakiye": "bakiye",
    "bakiye": "bakiye",
    # Döviz Tutar
    "detaytutardvz": "doviz_tutar",
    "doviztutar": "doviz_tutar",
    "doviz_tutar": "doviz_tutar",
    # Para Birim
    "detayparabirimkisaad": "para_birim",
    "parabirim": "para_birim",
    "para_birim": "para_birim",
    # Birim Adı (işyeri)
    "detaybirimad": "birim_adi",
    "birimad": "birim_adi",
    "birimadi": "birim_adi",
    # Özel Kod
    "detayozelkod": "ozel_kod",
    "ozelkod": "ozel_kod",
    # Ödeme Türü (ödeme şablon adı)
    "sablonad": "odeme_turu",
    "odemeturu": "odeme_turu",
    # Detay modal / islem acma
    "islemid": "islem_id",
    "modulkod": "modul_kod",
    "hareketmodultip": "modul_tip",
    "detaycarikartkod": "cari_kod",
    "detaycarikartad": "cari_unvan",
    "detaynettutar": "net_tutar",
    "detaykdvtutar": "kdv_tutar",
    "detayhareketbelgekod": "islem_belge_kod",
    "carifinansdetayid": "finans_detay_id",
    "bankafishareketid": "finans_detay_id",
    "banka_fis_hareket_id": "finans_detay_id",
    "bfhareketislemid": "islem_id",
    "bankafisid": "islem_id",
    "detayhareketturid": "hareket_tur_id",
    "hareketturid": "hareket_tur_id",
    "carifinansid": "cari_finans_id",
    "kasahareketid": "kasa_hareket_id",
}

# KASA_CARI_FIS -> kasa hareket detay
_KASA_FIS_COL_KEYS = {
    "kasahareketid": "kasa_hareket_id",
    "khack": "aciklama",
    "khackeki": "aciklama_ek",
    "khhareketturid": "hareket_tur_id",
    "khhareketturad": "hareket_tur_ad",
    "khformtur": "islem_form_tur",
    "khislemturid": "islem_tur_id",
    "khbelgeno": "belge_no",
    "khborcluadi": "borclu_adi",
    "khtrh": "tarih",
    "kasakod": "kasa_kod",
    "khkarsikasakod": "karsi_kasa_kod",
    "khmakbuzseri": "makbuz_seri",
    "khmakbuztrh": "makbuz_tarih",
    "khnettutar": "net_tutar",
    "khozelkod": "ozel_kod",
    "khozelno": "ozel_no",
    "khsaat": "saat",
    "khteslimeden": "teslim_eden",
    "khtutar": "tutar",
    "khtutardvz": "tutar_dvz",
    "khkasaad": "kasa_ad",
    "khbirimad": "birim_ad",
    "khcarikartad": "cari_unvan",
    "khcarikartkodu": "cari_kod",
    "khparabirimkisaad": "para_birim",
    "khparabirimkod": "para_birim_kod",
    "bankaadi": "banka_adi",
    "bankasubead": "banka_sube_ad",
    "bankahesapadi": "banka_hesap_adi",
    "bankahesapno": "banka_hesap_no",
    "khfaturano": "fatura_no",
    "khhareketturba": "ba",
    "khkdvoran": "kdv_oran",
    "khkdvtutar": "kdv_tutar",
    "odemeturu": "odeme_turu",
    "khislemno": "islem_no",
    "makbuzkisi": "makbuz_kisi",
    "yazdirmadurum": "yazdirma_durum",
    "makbuzdurum": "makbuz_durum",
}

# ALIS_FATURASI_MASTER -> fatura baslik
_ALIS_FATURA_MASTER_COL_KEYS = {
    "stokfsid": "fis_id",
    "stokfsfaturano": "fatura_no",
    "stokfsfaturatarihi": "fatura_tarihi",
    "stokfsbelgeno": "belge_no",
    "stokfsbelgetarihi": "belge_tarihi",
    "stokfsaciklama": "aciklama",
    "stokfscarikod": "cari_kod",
    "stokfscariad": "cari_unvan",
    "stokfsbirimad": "birim_adi",
    "stokfsgirisbirimad": "giris_birim_adi",
    "stokfstedarikturad": "hareket_tur_ad",
    "hareketbelgekod": "islem_belge_kod",
    "stokfstoplammatrah": "toplam_matrah",
    "stokfstoplamkdv": "toplam_kdv",
    "stokfsnettoplam": "net_toplam",
    "stokfsozelkod": "ozel_kod",
    "stokfsalisyontemad": "alis_yontem",
    "stokfsbutceturad": "butce_tur",
    "stokfsfiskod": "fis_kod",
    "stokfsfistarihi": "fis_tarihi",
    "faturairsaliyetarihi": "fatura_irsaliye_tarihi",
}

# ALIS_FATURASI_DETAY -> fatura satirlari
_ALIS_FATURA_DETAY_COL_KEYS = {
    "stokhareketid": "satir_id",
    "shstokkod": "stok_kod",
    "shstokad": "stok_ad",
    "shkdvoran": "kdv_oran",
    "shmiktar": "miktar",
    "shfiyat": "birim_fiyat",
    "shkdvmatrah": "matrah",
    "shtoplam": "toplam",
    "shkdvnettutar": "kdv_tutar",
    "sholcubirimad": "olcu_birim",
    "shaciklama": "aciklama",
    "shstokaciklama": "stok_aciklama",
}


# BANKA_CARI_FIS -> fis baslik
_BANKA_FIS_COL_KEYS = {
    "bankafisid": "banka_fis_id",
    "bankafisno": "banka_fis_no",
    "bankafistrh": "banka_fis_tarih",
    "bankafisack": "banka_fis_ack",
    "bankafistoplamborc": "toplam_borc",
    "bankafistoplamalacak": "toplam_alacak",
    "hareketturad": "hareket_tur_ad",
    "hareketbelgekod": "hareket_belge_kod",
    "birimad": "birim_ad",
    "firmakodu": "firma_kodu",
    "firmaadi": "firma_adi",
}

# BANKA_CARIF_FIS_HAREKET -> fis satirlari
_BANKA_HAREKET_COL_KEYS = {
    "bankahesapadi": "banka_hesap_adi",
    "bankaadi": "banka_adi",
    "firmakodu": "firma_kodu",
    "firmaadi": "firma_adi",
    "bfhareketborctutar": "borc",
    "bfhareketalacaktutar": "alacak",
    "bfhareketbelgeno": "belge_no",
    "bfhareketack": "aciklama",
    "bfhareketozelkod": "ozel_kod",
    "bfharekettrh": "tarih",
    "parabirimkisaad": "para_birim",
}

# CARI_FINANS -> fis baslik
_CARI_FINANS_COL_KEYS = {
    "carifinansid": "cari_finans_id",
    "carihareketturid": "hareket_tur_id",
    "carihareketturad": "hareket_tur_ad",
    "cariaciklama": "aciklama",
    "cariborc": "toplam_borc",
    "carialacak": "toplam_alacak",
    "caritarih": "tarih",
    "cariozelkod": "ozel_kod",
    "islemkod": "islem_kod",
    "caridurum": "durum",
}

# CARI_FINANS_DETAY -> fis satirlari
_CARI_FINANS_DETAY_COL_KEYS = {
    "detaycarikartkod": "cari_kod",
    "detaycarikartad": "cari_unvan",
    "detaybelgeno": "belge_no",
    "detayaciklama": "aciklama",
    "detayozelkod": "ozel_kod",
    "detayborctutar": "borc",
    "detayalacaktutar": "alacak",
    "detayfaturano": "fatura_no",
    "detaytarih": "tarih",
}


def _rename_columns(df, mapping):
    if df is None or df.empty:
        return df
    out = df.copy()
    rename = {}
    targets_used = set()
    for col in list(out.columns):
        canonical = mapping.get(_col_key(col))
        if not canonical or col == canonical:
            if col in mapping.values():
                targets_used.add(col)
            continue
        if canonical in targets_used:
            continue
        if canonical in out.columns and col != canonical:
            continue
        rename[col] = canonical
        targets_used.add(canonical)
    if rename:
        out = out.rename(columns=rename)
    return out


def _format_date_value(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return ""
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(text[:19], fmt).strftime("%d.%m.%Y")
            except ValueError:
                continue
        return text
    try:
        ts = pd.to_datetime(value, errors="coerce")
        if pd.isna(ts):
            return str(value).strip()
        return ts.strftime("%d.%m.%Y")
    except Exception:
        return str(value).strip()


def _tr_number(value, decimals=2):
    """Sayıyı 1.234.567,89 formatında döndürür."""
    formatted = f"{value:,.{decimals}f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def _format_bakiye(value):
    """Yürüyen bakiye (sayısal) -> '1.234,56 (A)' / '1.234,56 (B)' / '0,00'."""
    num = pd.to_numeric(value, errors="coerce")
    if pd.isna(num):
        text = str(value or "").strip()
        return text
    num = float(num)
    if num > 0.0049:
        suffix = " (A)"
    elif num < -0.0049:
        suffix = " (B)"
    else:
        suffix = ""
    return _tr_number(abs(num), 2) + suffix


def _normalize_ba(value):
    """DETAY_BA (0/1) -> 'B'/'A'. Devir vb. metinleri de tolere eder."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip().upper()
    if text in ("1", "1.0", "A", "ALACAK"):
        return "A"
    if text in ("0", "0.0", "B", "BORC", "BORÇ"):
        return "B"
    return text


def _safe_read_sql(conn, sql):
    """CARI sorgulari placeholder'lari metne basili geldigi icin '?' parametre kullanmaz."""
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="pandas only supports SQLAlchemy connectable",
            category=UserWarning,
        )
        return pd.read_sql(sql, conn)


def _arama_text(arama_metni):
    # Tek tirnak canli SQL'i kirmasin diye kacis ('' SQL Server'da literal tirnak).
    return str(arama_metni or "").strip().replace("'", "''")


def _arama_params(arama_text):
    return {
        # SQL: like '%' + @FIRMA_AD@ + '%'  -> yalnizca arama metni gonderilir
        "FIRMA_AD": arama_text,
        "firma_ad": arama_text,
        # Olasi alternatif placeholder adlari
        "ARAMA": arama_text,
        "FIRMA_UNVAN": arama_text,
        "CARI_UNVAN": arama_text,
    }


def _sql_teshis(sql):
    """Teshis icin SQL'in filtre (WHERE) kismini kisaltarak dondurur."""
    if not sql:
        return "(bos sql)"
    text = " ".join(str(sql).split())
    low = text.lower()
    idx = low.rfind(" where ")
    snippet = text[idx:] if idx != -1 else text
    return snippet[:600]


def _hareket_params(cari_id, start_date_str, end_date_str):
    cid = str(cari_id or "").strip()
    return {
        "start_date": start_date_str,
        "end_date": end_date_str,
        "BASLANGIC_TRH": start_date_str,
        "BITIS_TRH": end_date_str,
        "BAS_TRH": start_date_str,
        "BIT_TRH": end_date_str,
        # DETAY_CARI_KART_ID = @FIRMA_ID@  (ic id)
        "FIRMA_ID": cid,
        "firma_id": cid,
        "CARI_KART_ID": cid,
    }


def df_to_cari_listesi(df):
    if df is None or df.empty:
        return []
    normalized = _rename_columns(df, _CARI_LISTE_COL_KEYS)
    cols = normalized.columns

    id_col = "id" if "id" in cols else None
    kod_col = "kod" if "kod" in cols else None
    unvan_col = "unvan" if "unvan" in cols else None

    if not id_col and not kod_col:
        print(f"UYARI: cari arama — id/kod kolonu yok. Kolonlar: {list(cols)}")
        return []

    items = []
    seen = set()
    for row in normalized.to_dict(orient="records"):
        raw_id = row.get(id_col) if id_col else None
        cid = "" if raw_id is None or (isinstance(raw_id, float) and pd.isna(raw_id)) else str(raw_id).strip()
        if cid.endswith(".0") and cid[:-2].isdigit():
            cid = cid[:-2]

        kod = str(row.get(kod_col) or "").strip() if kod_col else ""
        # Hareket sorgusu ic id ile filtreledigi icin id zorunlu; yoksa kod'a düş.
        filter_id = cid or kod
        if not filter_id:
            continue

        unvan = str(row.get(unvan_col) or kod or filter_id).strip() if unvan_col else (kod or filter_id)
        display_kod = kod or cid

        dedup_key = filter_id
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        items.append({"id": filter_id, "kod": display_kod, "unvan": unvan})

    items.sort(key=lambda x: x["unvan"].casefold())
    return items


def df_to_hareket_listesi(df):
    if df is None or df.empty:
        return []
    normalized = _rename_columns(df, _HAREKET_COL_KEYS)
    rows = []
    for row in normalized.to_dict(orient="records"):
        ba = _normalize_ba(row.get("ba"))

        tutar = pd.to_numeric(row.get("tutar"), errors="coerce")
        tutar_val = float(tutar) if pd.notna(tutar) else 0.0
        net_tutar = pd.to_numeric(row.get("net_tutar"), errors="coerce")
        kdv_tutar = pd.to_numeric(row.get("kdv_tutar"), errors="coerce")
        net_val = float(net_tutar) if pd.notna(net_tutar) else tutar_val
        kdv_val = float(kdv_tutar) if pd.notna(kdv_tutar) else 0.0

        rows.append(
            {
                "modul": str(row.get("modul") or "").strip(),
                "tarih": _format_date_value(row.get("tarih")),
                "fatura_no": str(row.get("fatura_no") or "").strip(),
                "belge_no": str(row.get("belge_no") or "").strip(),
                "belge_tarihi": _format_date_value(row.get("belge_tarihi")),
                "vade_tarihi": _format_date_value(row.get("vade_tarihi")),
                "aciklama": str(row.get("aciklama") or "").strip(),
                "islem_turu": str(row.get("islem_turu") or "").strip(),
                "ba": ba,
                "tutar": tutar_val,
                "bakiye": _format_bakiye(row.get("bakiye")),
                "doviz_tutar": str(row.get("doviz_tutar") or "").strip(),
                "para_birim": str(row.get("para_birim") or "").strip() or "TL",
                "birim_adi": str(row.get("birim_adi") or "").strip(),
                "ozel_kod": str(row.get("ozel_kod") or "").strip(),
                "odeme_turu": str(row.get("odeme_turu") or "").strip(),
                "islem_id": str(row.get("islem_id") or "").strip(),
                "modul_kod": str(row.get("modul_kod") or "").strip(),
                "modul_tip": str(row.get("modul_tip") or "").strip(),
                "cari_kod": str(row.get("cari_kod") or "").strip(),
                "cari_unvan": str(row.get("cari_unvan") or "").strip(),
                "net_tutar": net_val,
                "kdv_tutar": kdv_val,
                "islem_belge_kod": str(row.get("islem_belge_kod") or "").strip(),
                "finans_detay_id": str(row.get("finans_detay_id") or "").strip(),
                "hareket_tur_id": str(row.get("hareket_tur_id") or "").strip(),
                "cari_finans_id": str(row.get("cari_finans_id") or row.get("islem_id") or "").strip(),
                "kasa_hareket_id": str(row.get("kasa_hareket_id") or row.get("islem_id") or "").strip(),
            }
        )
    return rows


@ttl_cache(maxsize=64, ttl=120)
def cari_firma_ara(arama_metni, start_date_str, end_date_str):
    arama_metni = str(arama_metni or "").strip()
    if not arama_metni:
        return []

    conn = baglanti_olustur()
    if not conn:
        return []

    try:
        arama_text = _arama_text(arama_metni)
        sql = get_remote_sql(
            "cari_sorusturma.cari_firma_ara",
            _arama_params(arama_text),
        )
        if not sql:
            return []

        df = _safe_read_sql(conn, sql)
        if not df.empty:
            print(
                f"[CARI_FIRMA_ARAMA] q={arama_metni!r} rows={len(df)} "
                f"cols={list(df.columns)}"
            )
        return df_to_cari_listesi(df)
    except Exception as exc:
        print(f"Cari firma arama hatasi ({arama_metni!r}): {exc}")
        return []
    finally:
        conn.close()


@ttl_cache(maxsize=64, ttl=60)
def cari_hareketleri_yukle(cari_id, start_date_str, end_date_str):
    cari_id = str(cari_id or "").strip()
    if not cari_id:
        return []

    conn = baglanti_olustur()
    if not conn:
        return []

    try:
        sql = get_remote_sql(
            "cari_sorusturma.cari_hareketleri_yukle",
            _hareket_params(cari_id, start_date_str, end_date_str),
        )
        if not sql:
            return []

        df = _safe_read_sql(conn, sql)
        print(
            f"[CARI_FIRMA_SORUSTURMA] firma_id={cari_id!r} "
            f"donem={start_date_str}..{end_date_str} rows={0 if df is None else len(df)} "
            f"cols={[] if df is None else list(df.columns)}"
        )
        if df is None or df.empty:
            # Bos donduyse: calisan SQL'in filtre kismini gorelim (teshis amacli).
            print(f"[CARI_FIRMA_SORUSTURMA][BOS] {_sql_teshis(sql)}")
        return df_to_hareket_listesi(df)
    except Exception as exc:
        print(f"Cari hareketleri yukleme hatasi ({cari_id}): {exc}")
        return []
    finally:
        conn.close()


def _num_value(value, default=0.0):
    num = pd.to_numeric(value, errors="coerce")
    return float(num) if pd.notna(num) else default


def _sql_int_literal(value):
    text = str(value or "").strip()
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    if not text.isdigit():
        return None
    return text


def _df_record_to_fis(row):
    if not row:
        return None
    return {
        "banka_fis_id": str(row.get("banka_fis_id") or "").strip(),
        "banka_fis_no": str(row.get("banka_fis_no") or "").strip(),
        "banka_fis_tarih": _format_date_value(row.get("banka_fis_tarih")),
        "banka_fis_ack": str(row.get("banka_fis_ack") or "").strip(),
        "toplam_borc": _num_value(row.get("toplam_borc")),
        "toplam_alacak": _num_value(row.get("toplam_alacak")),
        "hareket_tur_ad": str(row.get("hareket_tur_ad") or "").strip(),
        "hareket_belge_kod": str(row.get("hareket_belge_kod") or "").strip(),
        "birim_ad": str(row.get("birim_ad") or "").strip(),
        "firma_kodu": str(row.get("firma_kodu") or "").strip(),
        "firma_adi": str(row.get("firma_adi") or "").strip(),
    }


def _lookup_banka_ids(conn, hareket_id_giris):
    """
    CARI hareket satirindaki islemId aslinda BANKA_FIS_HAREKET_ID'dir.
    Bu hareketten, fis(islem) ID'sini (BF_HAREKET_ISLEM_ID = BANKA_FIS_ID) buluruz.

    Donus: (banka_fis_hareket_id, fis_islem_id)
      - banka_fis_hareket_id -> BANKA_CARI_FIS icin @bankafishareketId
      - fis_islem_id          -> BANKA_CARIF_FIS_HAREKET icin @BF_HAREKET_ISLEM_ID
    """
    hid = _sql_int_literal(hareket_id_giris)
    if not hid:
        return None, None

    sql = f"""
    SELECT TOP 1
        BANKA_FIS_HAREKET_ID AS hareket_id,
        BF_HAREKET_ISLEM_ID  AS fis_id
    FROM BANKA_FIS_HAREKET WITH (NOLOCK)
    WHERE ISNULL(PSF_ID, 0) = 0 AND BANKA_FIS_HAREKET_ID = {hid}
    """
    try:
        df = _safe_read_sql(conn, sql)
        if df is not None and not df.empty:
            row = df.iloc[0]
            return (
                _sql_int_literal(row.get("hareket_id")) or hid,
                _sql_int_literal(row.get("fis_id")),
            )
    except Exception as exc:
        print(f"[BANKA_ID_LOOKUP] hareket_id={hid} hata: {exc}")

    return hid, None


def _banka_fis_response(fis, hareketler, banka_fis_hareket_id="", islem_id=""):
    return {
        "fis": fis,
        "hareketler": hareketler,
        "count": len(hareketler),
        "debug_ids": {
            "banka_fis_hareket_id": banka_fis_hareket_id,
            "islem_id": islem_id,
        },
    }


def _df_to_banka_hareket_listesi(df):
    if df is None or df.empty:
        return []
    normalized = _rename_columns(df, _BANKA_HAREKET_COL_KEYS)
    rows = []
    for row in normalized.to_dict(orient="records"):
        rows.append(
            {
                "banka_hesap_adi": str(row.get("banka_hesap_adi") or "").strip(),
                "banka_adi": str(row.get("banka_adi") or "").strip(),
                "firma_kodu": str(row.get("firma_kodu") or "").strip(),
                "firma_adi": str(row.get("firma_adi") or "").strip(),
                "borc": _num_value(row.get("borc")),
                "alacak": _num_value(row.get("alacak")),
                "belge_no": str(row.get("belge_no") or "").strip(),
                "aciklama": str(row.get("aciklama") or "").strip(),
                "ozel_kod": str(row.get("ozel_kod") or "").strip(),
                "tarih": _format_date_value(row.get("tarih")),
                "para_birim": str(row.get("para_birim") or "").strip(),
            }
        )
    return rows


def _fetch_banka_hareket_satirlari_yedek(conn, fis_islem_id):
    """
    Rapor API BANKA_CARIF_FIS_HAREKET sorgusu 0 satir dondururse yedek.
    Ayni kolonlar; TUR_DETAY ic ice join yerine LEFT JOIN (orijinal SQL'de INNER JOIN satirlari siliyor).
    """
    fid = _sql_int_literal(fis_islem_id)
    if not fid:
        return []
    sql = f"""
    SELECT
        bd.DETAY_AD AS bankaHesapAdi,
        b.BANKA_AD AS bankaAdi,
        ck.CARI_KART_KODU AS firmaKodu,
        ck.CARI_KART_ADI AS firmaAdi,
        CASE WHEN bfh.BF_HAREKET_BA = 0 THEN bfh.BF_HAREKET_TUTAR ELSE 0 END AS bfHareketBorcTutar,
        CASE WHEN bfh.BF_HAREKET_BA = 1 THEN bfh.BF_HAREKET_TUTAR ELSE 0 END AS bfHareketAlacakTutar,
        bfh.BF_HAREKET_BELGE_NO AS bfHareketBelgeNo,
        bfh.BF_HAREKET_ACK AS bfHareketAck,
        bfh.BF_HAREKET_OZEL_KOD AS bfHareketOzelKod,
        bfh.BF_HAREKET_TRH AS bfHareketTrh,
        pb.PARA_BIRIM_KISA_AD AS paraBirimKisaAd
    FROM BANKA_FIS_HAREKET bfh WITH (NOLOCK)
    LEFT JOIN BANKA_DETAY bd WITH (NOLOCK)
      ON bd.BANKA_DETAY_ID = bfh.BF_HAREKET_BANKA_HESAP_ID AND ISNULL(bd.PSF_ID, 0) = 0
    LEFT JOIN BANKA b WITH (NOLOCK)
      ON b.BANKA_ID = bd.BANKA_ID AND ISNULL(b.PSF_ID, 0) = 0
    LEFT JOIN CARI_KART ck WITH (NOLOCK)
      ON ck.CARI_KART_ID = bfh.BF_HAREKET_CARI_KART_ID AND ISNULL(ck.PSF_ID, 0) = 0
    LEFT JOIN PARA_BIRIM pb WITH (NOLOCK)
      ON pb.PARA_BIRIM_ID = bd.PARA_BIRIM_ID AND ISNULL(pb.PSF_ID, 0) = 0
    WHERE ISNULL(bfh.PSF_ID, 0) = 0 AND bfh.BF_HAREKET_ISLEM_ID = {fid}
    ORDER BY bfh.BF_HAREKET_SIRA
    """
    try:
        df = _safe_read_sql(conn, sql)
        rows = _df_to_banka_hareket_listesi(df)
        if rows:
            print(f"[BANKA_HAREKET_YEDEK] fis_id={fid} rows={len(rows)}")
        return rows
    except Exception as exc:
        print(f"[BANKA_HAREKET_YEDEK] fis_id={fid} hata: {exc}")
        return []


def _banka_fis_params(banka_fis_hareket_id):
    bid = str(banka_fis_hareket_id or "").strip()
    return {
        "bankafishareketId": bid,
        "BANKA_FIS_HAREKET_ID": bid,
        "banka_fis_hareket_id": bid,
    }


def _banka_fis_hareket_params(islem_id):
    iid = str(islem_id or "").strip()
    return {
        "BF_HAREKET_ISLEM_ID": iid,
        "bf_hareket_islem_id": iid,
        "bfHareketIslemId": iid,
        "islem_id": iid,
    }


def _substitute_at_params(sql, params):
    """
    Rapor SQL'deki @TOKEN / @TOKEN@ placeholder'larini degerle degistirir.
    BANKA sorgularinda sonda @ olmayan parametreler icin (or: @bankafishareketId).
    """
    if not sql or not params:
        return sql
    out = str(sql)
    for key, raw in params.items():
        val = str(raw or "").strip()
        if not val:
            continue
        if val.isdigit():
            repl = val
        else:
            repl = "'" + val.replace("'", "''") + "'"
        for token in (key, key.lower(), key.upper()):
            out = out.replace(f"@{token}@", repl)
            out = out.replace(f"'@{token}'", repl if repl.startswith("'") else f"'{val.replace(chr(39), chr(39)+chr(39))}'")
            # Sonda @ olmayan token: =@bankafishareketId )
            out = re.sub(
                re.escape(f"@{token}") + r"(?![A-Za-z0-9_])",
                repl,
                out,
                flags=re.IGNORECASE,
            )
    return out


@ttl_cache(maxsize=128, ttl=60)
def banka_fis_detay_yukle(
    banka_fis_hareket_id=None,
    islem_id=None,
    cari_finans_detay_id=None,
    cari_kart_id=None,
):
    banka_fis_hareket_id = str(banka_fis_hareket_id or "").strip()
    islem_id = str(islem_id or "").strip()
    cari_finans_detay_id = str(cari_finans_detay_id or "").strip()
    cari_kart_id = str(cari_kart_id or "").strip()

    if not banka_fis_hareket_id and not islem_id and not cari_finans_detay_id:
        return _banka_fis_response(None, [], "", "")

    conn = baglanti_olustur()
    if not conn:
        return _banka_fis_response(None, [], banka_fis_hareket_id, islem_id)

    fis = None
    hareketler = []

    # Cari satirindaki islemId aslinda BANKA_FIS_HAREKET_ID; oncelikle onu kullan.
    hareket_id_giris = islem_id or banka_fis_hareket_id or cari_finans_detay_id

    try:
        # 165979 (hareket) -> 100204 (fis) cevirisi
        banka_fis_hareket_id, fis_islem_id = _lookup_banka_ids(conn, hareket_id_giris)
        islem_id = fis_islem_id or ""

        if banka_fis_hareket_id:
            fis_params = _banka_fis_params(banka_fis_hareket_id)
            sql_fis = get_remote_sql(
                "cari_sorusturma.banka_cari_fis",
                fis_params,
            )
            if sql_fis:
                sql_fis = _substitute_at_params(sql_fis, fis_params)
                df_fis = _safe_read_sql(conn, sql_fis)
                if df_fis is not None and not df_fis.empty:
                    normalized = _rename_columns(df_fis, _BANKA_FIS_COL_KEYS)
                    fis = _df_record_to_fis(normalized.iloc[0].to_dict())
                    if not islem_id:
                        islem_id = str(fis.get("banka_fis_id") or "").strip()

        if islem_id:
            har_params = _banka_fis_hareket_params(islem_id)
            sql_har = get_remote_sql(
                "cari_sorusturma.banka_cari_fis_hareket",
                har_params,
            )
            if sql_har:
                sql_har = _substitute_at_params(sql_har, har_params)
                df_har = _safe_read_sql(conn, sql_har)
                hareketler = _df_to_banka_hareket_listesi(df_har)
                print(
                    f"[BANKA_CARIF_FIS_HAREKET] giris={hareket_id_giris!r} "
                    f"hareket_id={banka_fis_hareket_id!r} fis_id={islem_id!r} "
                    f"rows={len(hareketler)}"
                )

        if not hareketler and islem_id:
            hareketler = _fetch_banka_hareket_satirlari_yedek(conn, islem_id)

        return _banka_fis_response(fis, hareketler, banka_fis_hareket_id, islem_id)
    except Exception as exc:
        print(
            f"Banka fis detay hatasi (hareket_id={banka_fis_hareket_id!r}, "
            f"islem_id={islem_id!r}, cari_finans_detay_id={cari_finans_detay_id!r}): {exc}"
        )
        return _banka_fis_response(fis, hareketler, banka_fis_hareket_id, islem_id)
    finally:
        conn.close()


def _df_record_to_cari_finans(row):
    if not row:
        return None
    return {
        "cari_finans_id": str(row.get("cari_finans_id") or "").strip(),
        "hareket_tur_id": str(row.get("hareket_tur_id") or "").strip(),
        "hareket_tur_ad": str(row.get("hareket_tur_ad") or "").strip(),
        "aciklama": str(row.get("aciklama") or "").strip(),
        "toplam_borc": _num_value(row.get("toplam_borc")),
        "toplam_alacak": _num_value(row.get("toplam_alacak")),
        "tarih": _format_date_value(row.get("tarih")),
        "ozel_kod": str(row.get("ozel_kod") or "").strip(),
        "islem_kod": str(row.get("islem_kod") or "").strip(),
        "durum": str(row.get("durum") or "").strip(),
    }


def _df_to_cari_finans_detay_listesi(df):
    if df is None or df.empty:
        return []
    normalized = _rename_columns(df, _CARI_FINANS_DETAY_COL_KEYS)
    rows = []
    for row in normalized.to_dict(orient="records"):
        kod = str(row.get("cari_kod") or "").strip()
        unvan = str(row.get("cari_unvan") or "").strip()
        rows.append(
            {
                "cari_kod": kod,
                "cari_unvan": unvan,
                "cari_kod_unvan": (kod + " - " + unvan).strip(" -") if (kod or unvan) else "",
                "belge_no": str(row.get("belge_no") or "").strip(),
                "aciklama": str(row.get("aciklama") or "").strip(),
                "ozel_kod": str(row.get("ozel_kod") or "").strip(),
                "borc": _num_value(row.get("borc")),
                "alacak": _num_value(row.get("alacak")),
                "fatura_no": str(row.get("fatura_no") or "").strip(),
                "tarih": _format_date_value(row.get("tarih")),
            }
        )
    return rows


def _cari_finans_params(cari_finans_id):
    cid = str(cari_finans_id or "").strip()
    return {
        "CARI_FINANS_ID": cid,
        "cari_finans_id": cid,
        "carifinansId": cid,
    }


def _cari_finans_detay_params(cari_finans_id, hareket_tur_id):
    fid = str(cari_finans_id or "").strip()
    tid = str(hareket_tur_id or "").strip()
    return {
        "CARI_FINANS_DETAY_ID": fid,
        "CARI_FINANS_ID": fid,
        "cari_finans_id": fid,
        "HAREKET_TUR_ID": tid,
        "hareket_tur_id": tid,
        "hareketTurId": tid,
    }


def _cari_finans_response(fis, hareketler):
    return {
        "fis": fis,
        "hareketler": hareketler,
        "count": len(hareketler),
    }


@ttl_cache(maxsize=128, ttl=60)
def cari_finans_detay_yukle(cari_finans_id, hareket_tur_id=None):
    cari_finans_id = str(cari_finans_id or "").strip()
    hareket_tur_id = str(hareket_tur_id or "").strip()
    if not cari_finans_id:
        return _cari_finans_response(None, [])

    conn = baglanti_olustur()
    if not conn:
        return _cari_finans_response(None, [])

    fis = None
    hareketler = []
    try:
        fis_params = _cari_finans_params(cari_finans_id)
        sql_fis = get_remote_sql("cari_sorusturma.cari_finans", fis_params)
        if sql_fis:
            sql_fis = _substitute_at_params(sql_fis, fis_params)
            df_fis = _safe_read_sql(conn, sql_fis)
            if df_fis is not None and not df_fis.empty:
                normalized = _rename_columns(df_fis, _CARI_FINANS_COL_KEYS)
                fis = _df_record_to_cari_finans(normalized.iloc[0].to_dict())
                if not hareket_tur_id:
                    hareket_tur_id = str(fis.get("hareket_tur_id") or "").strip()

        if cari_finans_id and hareket_tur_id:
            det_params = _cari_finans_detay_params(cari_finans_id, hareket_tur_id)
            sql_det = get_remote_sql("cari_sorusturma.cari_finans_detay", det_params)
            if sql_det:
                sql_det = _substitute_at_params(sql_det, det_params)
                df_det = _safe_read_sql(conn, sql_det)
                hareketler = _df_to_cari_finans_detay_listesi(df_det)
                print(
                    f"[CARI_FINANS_DETAY] finans_id={cari_finans_id!r} "
                    f"tur_id={hareket_tur_id!r} rows={len(hareketler)}"
                )

        return _cari_finans_response(fis, hareketler)
    except Exception as exc:
        print(
            f"Cari finans detay hatasi (finans_id={cari_finans_id!r}, "
            f"tur_id={hareket_tur_id!r}): {exc}"
        )
        return _cari_finans_response(fis, hareketler)
    finally:
        conn.close()


def _df_record_to_kasa_fis(row):
    if not row:
        return None
    aciklama = str(row.get("aciklama") or "").strip()
    ek = str(row.get("aciklama_ek") or "").strip()
    if ek and ek not in aciklama:
        aciklama = (aciklama + " " + ek).strip()
    kod = str(row.get("cari_kod") or "").strip()
    unvan = str(row.get("cari_unvan") or "").strip()
    return {
        "kasa_hareket_id": str(row.get("kasa_hareket_id") or "").strip(),
        "hareket_tur_ad": str(row.get("hareket_tur_ad") or "").strip(),
        "hareket_tur_id": str(row.get("hareket_tur_id") or "").strip(),
        "islem_form_tur": str(row.get("islem_form_tur") or "").strip(),
        "islem_tur_id": str(row.get("islem_tur_id") or "").strip(),
        "tarih": _format_date_value(row.get("tarih")),
        "saat": str(row.get("saat") or "").strip(),
        "islem_no": str(row.get("islem_no") or "").strip(),
        "kasa_kod": str(row.get("kasa_kod") or "").strip(),
        "kasa_ad": str(row.get("kasa_ad") or "").strip(),
        "birim_ad": str(row.get("birim_ad") or "").strip(),
        "belge_no": str(row.get("belge_no") or "").strip(),
        "makbuz_seri": str(row.get("makbuz_seri") or "").strip(),
        "makbuz_tarih": _format_date_value(row.get("makbuz_tarih")),
        "odeme_turu": str(row.get("odeme_turu") or "").strip(),
        "para_birim": str(row.get("para_birim") or "").strip() or "TL",
        "cari_kod": kod,
        "cari_unvan": unvan,
        "cari_kod_unvan": (kod + " - " + unvan).strip(" -") if (kod or unvan) else "",
        "aciklama": aciklama,
        "ozel_kod": str(row.get("ozel_kod") or "").strip(),
        "ozel_no": str(row.get("ozel_no") or "").strip(),
        "tutar": _num_value(row.get("tutar")),
        "kdv_tutar": _num_value(row.get("kdv_tutar")),
        "net_tutar": _num_value(row.get("net_tutar")),
        "kdv_oran": str(row.get("kdv_oran") or "").strip(),
        "fatura_no": str(row.get("fatura_no") or "").strip(),
        "banka_adi": str(row.get("banka_adi") or "").strip(),
        "banka_sube_ad": str(row.get("banka_sube_ad") or "").strip(),
        "banka_hesap_adi": str(row.get("banka_hesap_adi") or "").strip(),
        "banka_hesap_no": str(row.get("banka_hesap_no") or "").strip(),
        "makbuz_kisi": str(row.get("makbuz_kisi") or "").strip(),
        "makbuz_durum": str(row.get("makbuz_durum") or "").strip(),
        "yazdirma_durum": str(row.get("yazdirma_durum") or "").strip(),
        "borclu_adi": str(row.get("borclu_adi") or "").strip(),
        "teslim_eden": str(row.get("teslim_eden") or "").strip(),
        "karsi_kasa_kod": str(row.get("karsi_kasa_kod") or "").strip(),
        "ba": _normalize_ba(row.get("ba")),
    }


def _kasa_fis_params(kasa_hareket_id):
    kid = str(kasa_hareket_id or "").strip()
    return {
        "KASA_HAREKET_ID": kid,
        "kasa_hareket_id": kid,
        "kasaHareketId": kid,
    }


def _kasa_fis_response(fis):
    return {
        "fis": fis,
        "count": 1 if fis else 0,
    }


@ttl_cache(maxsize=128, ttl=60)
def kasa_fis_detay_yukle(kasa_hareket_id=None):
    kasa_hareket_id = str(kasa_hareket_id or "").strip()
    if not kasa_hareket_id:
        return _kasa_fis_response(None)

    conn = baglanti_olustur()
    if not conn:
        return _kasa_fis_response(None)

    fis = None
    try:
        params = _kasa_fis_params(kasa_hareket_id)
        sql = get_remote_sql("cari_sorusturma.kasa_cari_fis", params)
        if sql:
            sql = _substitute_at_params(sql, params)
            df = _safe_read_sql(conn, sql)
            if df is not None and not df.empty:
                normalized = _rename_columns(df, _KASA_FIS_COL_KEYS)
                fis = _df_record_to_kasa_fis(normalized.iloc[0].to_dict())
                print(
                    f"[KASA_CARI_FIS] hareket_id={kasa_hareket_id!r} "
                    f"rows={len(df)}"
                )
        return _kasa_fis_response(fis)
    except Exception as exc:
        print(f"Kasa fis detay hatasi (hareket_id={kasa_hareket_id!r}): {exc}")
        return _kasa_fis_response(fis)
    finally:
        conn.close()


def _df_record_to_alis_fatura_master(row):
    if not row:
        return None
    birim = str(row.get("birim_adi") or row.get("giris_birim_adi") or "").strip()
    return {
        "fis_id": str(row.get("fis_id") or "").strip(),
        "fatura_no": str(row.get("fatura_no") or "").strip(),
        "fatura_tarihi": _format_date_value(
            row.get("fatura_tarihi") or row.get("fatura_irsaliye_tarihi")
        ),
        "belge_no": str(row.get("belge_no") or "").strip(),
        "belge_tarihi": _format_date_value(row.get("belge_tarihi")),
        "aciklama": str(row.get("aciklama") or "").strip(),
        "cari_kod": str(row.get("cari_kod") or "").strip(),
        "cari_unvan": str(row.get("cari_unvan") or "").strip(),
        "birim_adi": birim,
        "hareket_tur_ad": str(row.get("hareket_tur_ad") or "").strip(),
        "islem_belge_kod": str(row.get("islem_belge_kod") or row.get("fis_kod") or "").strip(),
        "toplam_matrah": _num_value(row.get("toplam_matrah")),
        "toplam_kdv": _num_value(row.get("toplam_kdv")),
        "net_toplam": _num_value(row.get("net_toplam")),
        "ozel_kod": str(row.get("ozel_kod") or "").strip(),
        "alis_yontem": str(row.get("alis_yontem") or "").strip(),
        "butce_tur": str(row.get("butce_tur") or "").strip(),
    }


def _df_to_alis_fatura_detay_listesi(df):
    if df is None or df.empty:
        return []
    normalized = _rename_columns(df, _ALIS_FATURA_DETAY_COL_KEYS)
    rows = []
    for row in normalized.to_dict(orient="records"):
        aciklama = str(row.get("aciklama") or row.get("stok_aciklama") or "").strip()
        matrah = _num_value(row.get("matrah"))
        if matrah <= 0:
            matrah = _num_value(row.get("toplam"))
        rows.append(
            {
                "satir_id": str(row.get("satir_id") or "").strip(),
                "stok_kod": str(row.get("stok_kod") or "").strip(),
                "stok_ad": str(row.get("stok_ad") or "").strip(),
                "kdv_oran": _num_value(row.get("kdv_oran")),
                "miktar": _num_value(row.get("miktar")),
                "birim_fiyat": _num_value(row.get("birim_fiyat")),
                "matrah": matrah,
                "kdv_tutar": _num_value(row.get("kdv_tutar")),
                "olcu_birim": str(row.get("olcu_birim") or "").strip(),
                "aciklama": aciklama,
            }
        )
    return rows


def _alis_fatura_params(fis_id):
    fid = str(fis_id or "").strip()
    return {
        "FIS_ID": fid,
        "fis_id": fid,
        "stokFsId": fid,
        "STOK_FS_ID": fid,
    }


def _alis_fatura_response(fis, satirlar):
    return {
        "fis": fis,
        "satirlar": satirlar,
        "count": len(satirlar),
    }


@ttl_cache(maxsize=128, ttl=60)
def alis_fatura_detay_yukle(fis_id=None):
    fis_id = str(fis_id or "").strip()
    if not fis_id:
        return _alis_fatura_response(None, [])

    conn = baglanti_olustur()
    if not conn:
        return _alis_fatura_response(None, [])

    fis = None
    satirlar = []
    try:
        params = _alis_fatura_params(fis_id)
        sql_master = get_remote_sql("cari_sorusturma.alis_faturasi_master", params)
        if sql_master:
            sql_master = _substitute_at_params(sql_master, params)
            df_master = _safe_read_sql(conn, sql_master)
            if df_master is not None and not df_master.empty:
                normalized = _rename_columns(df_master, _ALIS_FATURA_MASTER_COL_KEYS)
                fis = _df_record_to_alis_fatura_master(normalized.iloc[0].to_dict())
                print(f"[ALIS_FATURASI_MASTER] fis_id={fis_id!r} rows={len(df_master)}")

        sql_detay = get_remote_sql("cari_sorusturma.alis_faturasi_detay", params)
        if sql_detay:
            sql_detay = _substitute_at_params(sql_detay, params)
            df_detay = _safe_read_sql(conn, sql_detay)
            satirlar = _df_to_alis_fatura_detay_listesi(df_detay)
            print(
                f"[ALIS_FATURASI_DETAY] fis_id={fis_id!r} "
                f"rows={len(satirlar)}"
            )

        return _alis_fatura_response(fis, satirlar)
    except Exception as exc:
        print(f"Alis fatura detay hatasi (fis_id={fis_id!r}): {exc}")
        return _alis_fatura_response(fis, satirlar)
    finally:
        conn.close()
