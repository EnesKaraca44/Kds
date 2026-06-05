# -*- coding: utf-8 -*-
from flask import Blueprint, current_app, jsonify, render_template, request
from datetime import date, timedelta
import json
import re
import sys, os
import unicodedata
from pathlib import Path
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required
from database.tedavi_kartlari_sorgular import (
    tedavi_gruplari_dagilimi_grafik_yukle,
    tedavi_gruplari_dagilimi_yukle,
)
from routes.dashboard import get_date_range


tedavi_kartlari_bp = Blueprint('tedavi_kartlari', __name__)

PAGE_SQL_KODLARI = [
    "tedavi_kartlari.tedavi_gruplari_dagilimi",
    "tedavi_kartlari.tedavi_gruplari_dagilimi_grafik",
]

# Deploy dogrulama: servis logunda bu satiri gormezseniz eski .py calisiyordur.
TEDAVI_KARTLARI_BUILD = "2026-06-04-kart-degerleri-modal-align-v2"


def _load_tr_bundle():
    """Turkce metinler UTF-8 JSON'dan; sunucuda .py ANSI olsa bile dogru okunur."""
    path = Path(__file__).with_name("tedavi_kartlari_tr.json")
    if not path.exists():
        try:
            siblings = [p.name for p in Path(__file__).resolve().parent.glob("tedavi_kartlari_tr*.json")]
            print(
                "[TEDAVI_KARTLARI] tedavi_kartlari_tr.json bulunamadi. "
                f"beklenen={path}, bulunan_benzer={siblings}"
            )
        except Exception:
            pass
        raise FileNotFoundError(
            f"TR bundle eksik: {path}. Deploy paketine routes/tedavi_kartlari_tr.json dosyasini ekleyin."
        )
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


_TR = _load_tr_bundle()


def _write_deploy_stamp():
    """Servis hangi dosyayi calistiriyor - restart sonrasi dosyadan okunur (log gerekmez)."""
    stamp = Path(__file__).resolve().parent.parent / "tedavi_kartlari_deploy.stamp"
    body = (
        f"build={TEDAVI_KARTLARI_BUILD}\n"
        f"file={Path(__file__).resolve()}\n"
        f"json={Path(__file__).resolve().with_name('tedavi_kartlari_tr.json')}\n"
    )
    try:
        stamp.write_text(body, encoding="utf-8")
    except OSError as exc:
        print(f"[TEDAVI_KARTLARI] stamp yazilamadi: {exc}", flush=True)
    print(f"[TEDAVI_KARTLARI] loaded {TEDAVI_KARTLARI_BUILD} @ {Path(__file__).resolve()}", flush=True)


TEDAVI_KARTLARI_UI = _TR["ui"]
_CARD_ORDER = _TR["card_order"]
_DATA_COLUMN_TITLES = _TR["data_column_titles"]
_CARD_TITLE_RECETE_GRUP = _TR["card_title_recete_grup"]
_CARD_PERIOD_VALUE_FROM_GRAFIK = frozenset(_TR["card_period_from_grafik"])
_RECETE_GRUP_CARD_DEFS = tuple(tuple(x) for x in _TR["recete_grup_card_defs"])
_CARD_META = {k: tuple(v) for k, v in _TR["card_meta"].items()}
_WIDE_COLUMN_MAP = {k: tuple(v) for k, v in _TR["wide_column_map"].items()}
_RECETE_GRUP_ID_TO_AD = {int(k): v for k, v in _TR["recete_grup_id_to_ad"].items()}
# Kart basligi -> GRAFIK SQL genis kolon anahtarlari (or. EndodontikTedavi)
_CARD_TITLE_WIDE_COL_KEYS = {}
for _wkey, _wval in _WIDE_COLUMN_MAP.items():
    if not isinstance(_wval, (list, tuple)) or len(_wval) < 1:
        continue
    _wtitle = _wval[0]
    _CARD_TITLE_WIDE_COL_KEYS.setdefault(_wtitle, [])
    if _wkey not in _CARD_TITLE_WIDE_COL_KEYS[_wtitle]:
        _CARD_TITLE_WIDE_COL_KEYS[_wtitle].append(_wkey)

_SUT_KOD_COLUMNS = (
    "HIZMET_KODU", "HIZMETKODU", "HIZMET_SUT_KODU", "HIZMETSUTKODU", "SUT_KODU", "SUTKODU",
)
_SUT_TANIM_COLUMNS = (
    "HIZMET_SUT_TANIMI", "HIZMETSUTTANIMI", "HIZMET_SUT_TANIM", "SUT_TANIMI", "SUTTANIMI",
    "HIZMET_TANIMI", "HIZMETTANIMI",
)
_BUCKET_ORDER = _TR["bucket_titles"]
_ORDER_TO_TITLE = {int(order): title for title, order in _CARD_ORDER.items()}

_write_deploy_stamp()

_TITLE_COLUMNS = (
    "ISLEM_GRUBU", "İŞLEM_GRUBU", "BASLIK", "BAŞLIK", "ADI",
    "TETKIK_ADI", "TETKİK_ADI", "TEDAVI_GRUBU", "TEDAVİ_GRUBU",
    "TEDAVI_GRUBU_ADI", "TEDAVİ_GRUBU_ADI", "GRUP_ADI",
)
_VALUE_COLUMNS = (
    "ADET", "SAYI", "TOPLAM", "TOPLAM_ADET", "TOPLAM_ADEDI",
    "TOPLAM_ADEDİ", "ISLEM_ADETI", "İŞLEM_ADEDİ", "ISLEM_SAYISI",
    "İŞLEM_SAYISI", "TETKIK_ADET", "TETKİK_ADET", "HST_ADET",
    "DEGER", "DEĞER", "MIKTAR", "MİKTAR",
    "HIZMET_SAYISI", "HİZMET_SAYISI",
)
_CATEGORY_COLUMNS = (
    "KATEGORI", "KATEGORİ", "KATEGORI_ADI", "KATEGORİ_ADI",
    "KATEGORI_GRUBU", "KATEGORİ_GRUBU", "GRUP", "UST_GRUP", "ÜST_GRUP",
    "ANA_KATEGORI", "ANA_KATEGORİ", "UST_KATEGORI", "ÜST_KATEGORİ",
    "HIZMET_GRUBU", "HİZMET_GRUBU", "ISLEM_TURU", "İŞLEM_TÜRÜ",
)
_ORDER_COLUMNS = ("SIRA", "SIRALAMA", "ORDER_NO", "LISTE_SIRA")

_FALLBACK_COLORS = ("#2563eb", "#0891b2", "#16a34a", "#dc2626", "#7c3aed", "#ea580c", "#4f46e5", "#db2777", "#d97706", "#475569")
_DATA_COLUMN_RECETE_GRUP = {
    "DATA1": "47",
    "DATA2": "4",
    "DATA3": "7,10",
    "DATA4": "2,33",
    "DATA5": "1,11,23",
    "DATA6": "14,25",
    "DATA7": "32",
    "DATA8": "3",
    "DATA9": "9",
    "DATA10": "30",
    "DATA11": "31",
    "DATA12": "8",
    "DATA13": "29",
    "DATA14": "16",
    "DATA15": "12",
}


def _finalize_wide_numeric_rows(rows):
    """Serviste DATA16 gibi ozet kolonlar yanlis (806090); detay kolonlari tercih edilir."""
    cleaned = []
    for row in rows or []:
        title_key = _condense_alnum(row.get("title") or "")
        col_key = row.pop("_col_key", None) or ""
        rules = _WIDE_COLUMN_PRIORITY.get(title_key)
        if rules and col_key in rules.get("aggregate", frozenset()):
            continue
        cleaned.append(row)
    return _merge_card_rows(cleaned)


def _merge_recete_grup_kodu(prev, new):
    """Virgullu RECETE_GRUP_KODU listelerini birlestir (or. 15 + 34 -> 15,34)."""
    parts = []
    for chunk in (prev, new):
        chunk = str(chunk or "").strip()
        if not chunk:
            continue
        parts.extend(re.split(r"\s*,\s*", chunk))
    seen = set()
    ordered = []
    for part in parts:
        part = part.strip()
        if not part or part in seen:
            continue
        seen.add(part)
        ordered.append(part)
    return ",".join(ordered)


def pd_to_number(value):
    try:
        if pd.isna(value) or value == "":
            return 0.0
        numeric = float(value)
        if pd.isna(numeric):
            return 0.0
        return numeric
    except (TypeError, ValueError):
        return None


def _coerce_count(value, default=0):
    """Sayim alanlarini int'e cevir; serviste str gelince += birlestirme yapmasin (80+60 -> 806090)."""
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        pass
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value != value:
            return default
        return int(round(value))
    numeric = pd_to_number(value)
    if numeric is not None:
        return int(round(numeric))
    text = str(value).strip()
    if not text:
        return default
    try:
        return int(round(float(text.replace(",", "."))))
    except (TypeError, ValueError):
        return default


def _safe_int_sum(values):
    """pandas Series uzerinde str toplami (806090) yerine sayisal toplam."""
    if values is None:
        return 0
    if hasattr(values, "tolist"):
        try:
            values = values.tolist()
        except (TypeError, ValueError, AttributeError):
            pass
    total = 0
    for item in values:
        total += _coerce_count(item)
    return total


def _merge_card_rows(rows):
    """Ayni kart basligina sahip satirlari topla (YerTutucu + YerTutucuHareketli vb.)."""
    grouped = {}
    for row in rows or []:
        title = row.get("title")
        if not title:
            continue
        amount = _coerce_count(row.get("value"))
        if title not in grouped:
            grouped[title] = {
                "title": title,
                "value": amount,
                "category": row.get("category") or "",
                "recete_grup_kodu": str(row.get("recete_grup_kodu") or "").strip(),
            }
        else:
            grouped[title]["value"] += amount
            grouped[title]["recete_grup_kodu"] = _merge_recete_grup_kodu(
                grouped[title].get("recete_grup_kodu"),
                row.get("recete_grup_kodu"),
            )
            if row.get("category") and not grouped[title].get("category"):
                grouped[title]["category"] = row["category"]
    return list(grouped.values())


def _normalize_text(value):
    if pd.isna(value):
        return ""
    return _display_str(str(value or "").strip())


def _display_str(value):
    """Sunucuda bozulmus metinleri duzelt; NFC ile birlestir."""
    text = unicodedata.normalize("NFKC", str(value or ""))
    if not text:
        return ""
    if "?" not in text and "\ufffd" not in text:
        return text
    for enc in ("cp1254", "latin1"):
        try:
            repaired = text.encode(enc).decode("utf-8")
            if repaired.count("?") < text.count("?"):
                return unicodedata.normalize("NFKC", repaired)
        except (UnicodeDecodeError, UnicodeEncodeError):
            continue
    return text.replace("\ufffd", "")


def _card_icon_letter(title, category):
    """Windows serviste emoji yerine okunakli harf."""
    for source in (title, category):
        source = _display_str(source)
        for ch in source:
            if ch.isalnum():
                return ch.upper()
    return "T"


def _lookup_key(value):
    text = _normalize_text(value)
    # API / ODBC farkli Unicode birlesimleri (NFC/NFKC) gonderebiliyor; eslesmeyi stabilize et.
    text = unicodedata.normalize("NFKC", text).upper()
    for src, dst in (
        ("Ç", "C"), ("Ğ", "G"), ("İ", "I"), ("Ö", "O"), ("Ş", "S"), ("Ü", "U"),
        ("Â", "A"), ("Î", "I"), ("Û", "U"),
        ("ç", "c"), ("ğ", "g"), ("ı", "i"), ("ö", "o"), ("ş", "s"), ("ü", "u"),
    ):
        text = text.replace(src, dst)
    return text


def _slugify(value):
    slug = _lookup_key(value).lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return slug or "islem"


def _condense_alnum(value):
    """Harfleri buyut, Turkce'yi sadelestir, sadece harf+rakam birak (eslesme icin)."""
    return re.sub(r"[^A-Z0-9]", "", _lookup_key(value))


def _is_yer_tutucu_card(title, recete_grup_kodu=None):
    """Yer tutucu karti ve alt gruplari listeden cikarilir."""
    tk = _title_key(title or "")
    if tk == _title_key("Yer Tutucu Sayısı") or "YERTUTUCU" in tk:
        return True
    gid = re.sub(r"\s+", "", str(recete_grup_kodu or ""))
    return gid in ("15", "34", "15,34", "34,15")


def _filter_excluded_rows(rows):
    return [
        r
        for r in (rows or [])
        if not _is_yer_tutucu_card(r.get("title"), r.get("recete_grup_kodu"))
    ]


_WIDE_COLUMN_PRIORITY = {
    _condense_alnum("Ortodonti"): {
        "detail": frozenset({"ORTODONTI", "ORTODONTISABIT", "ORTODONTIHAREKETLI"}),
        "aggregate": frozenset(),
    },
}

# Bu kartlarda DAGILIMI'den gelen tek hücre değerine güvenme (serviste bozuluyor).
_FORCE_GRAFIK_TITLE_KEYS = frozenset({_condense_alnum("Ortodonti")})
_MAX_PLAUSIBLE_BY_TITLE = {
    _condense_alnum("Ortodonti"): 15000,
}


def _find_column(df, candidates):
    normalized = {str(col).strip().upper(): col for col in df.columns}
    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]
    # ODBC / driver bazen kose parantezli veya farkli bosluklu dondurur
    collapse = re.compile(r"[\s\[\]]+")

    def _key(c):
        return collapse.sub("", str(c).strip().upper())

    norm_collapsed = {_key(col): col for col in df.columns}
    for candidate in candidates:
        k = collapse.sub("", candidate.upper())
        if k in norm_collapsed:
            return norm_collapsed[k]
    return None


def _month_start(value):
    return date(value.year, value.month, 1)


def _add_months(value, months):
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def _month_ranges(end_date, month_count=6):
    month_names = (
        "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
        "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
    )
    first_month = _add_months(_month_start(end_date), -(month_count - 1))
    ranges = []
    for index in range(month_count):
        start = _add_months(first_month, index)
        next_start = _add_months(start, 1)
        end = next_start - timedelta(days=1)
        if index == month_count - 1:
            end = min(end, end_date)
        ranges.append((start, end, f"{month_names[start.month - 1]} {start.year}"))
    return ranges


def _graph_month_start(end_date, month_count=6):
    return _add_months(_month_start(end_date), -(month_count - 1))


def _period_for_chart_months(end_date, month_count=1, clip_start=None, clip_end=None):
    """
    Grafikte secilen son N ay (6 aylik pencere icinden).
    clip_start: sayfa filtresi baslangici (modal kirilimda kullanilmaz).
  """
    month_count = max(1, min(int(month_count or 1), 6))
    ed = end_date if isinstance(end_date, date) else _parse_iso_date(end_date)
    if not ed:
        return "", ""
    ranges = _month_ranges(ed, 6)
    if not ranges:
        return "", ""
    slice_ranges = ranges[-month_count:]
    start = slice_ranges[0][0]
    end = slice_ranges[-1][1]
    cs = clip_start if isinstance(clip_start, date) else _parse_iso_date(clip_start)
    ce = clip_end if isinstance(clip_end, date) else _parse_iso_date(clip_end)
    if cs and start < cs:
        start = cs
    if ce and end > ce:
        end = ce
    if start > end:
        return "", ""
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def _card_meta_for(title, category):
    key = _lookup_key(title)
    for marker, meta in _CARD_META.items():
        if marker in key:
            return meta

    bucket = _map_to_standard_bucket(title)
    if bucket:
        bk = _lookup_key(bucket)
        for marker, meta in _CARD_META.items():
            if marker in bk:
                return meta

    category_text = _normalize_text(category) or "Diğer"
    title_text = _display_str(title)
    return (
        category_text,
        "#475569",
        f"{title_text} işlem grubuna ait toplam işlem sayısı.",
    )


def _display_group_for(title):
    """Geriye donuk: bilinen dashboard kovasini dondurur; yoksa None."""
    return _map_to_standard_bucket(title)


def _title_for_bucket(bucket_key):
    """bucket_titles JSON'da kart sirasi (1-99) tutar; ekranda gosterilecek basliga cevir."""
    order = _BUCKET_ORDER.get(bucket_key)
    if order is None:
        return None
    try:
        return _ORDER_TO_TITLE.get(int(order))
    except (TypeError, ValueError):
        return None


def _map_to_standard_bucket(title):
    key = _lookup_key(title)
    if "PANORAMIK" in key:
        return _title_for_bucket("panoramik")
    if "PERIAPIKAL" in key:
        return _title_for_bucket("periapikal")
    if "MUAYENE" in key:
        return _title_for_bucket("muayene")
    if "ENDODONT" in key or "KANAL" in key:
        return _title_for_bucket("endodontik")
    if "DOLGU" in key or "KONSERVATIF" in key or "RESTORATIF" in key:
        return _title_for_bucket("konservatif")
    if "DIS CEKIM" in key or "CEKIM" in key:
        return _title_for_bucket("dis_cekim")
    if "FLEP" in key or "GING" in key or "OPERASYON" in key:
        return _title_for_bucket("operasyon")
    if "CERRAHI" in key:
        return _title_for_bucket("cerrahi")
    if "SABIT" in key and "PROTEZ" in key:
        return _title_for_bucket("sabit_protez")
    if "TOTAL" in key and ("PROTEZ" in key or "HAREKETLI" in key):
        return _title_for_bucket("hareketli_total")
    if "PARSIYEL" in key and ("PROTEZ" in key or "HAREKETLI" in key):
        return _title_for_bucket("hareketli_parsiyel")
    if "DETERTRAJ" in key or "DIS TASI" in key:
        return _title_for_bucket("detertraj")
    if "KURETAJ" in key:
        return _title_for_bucket("kuretaj")
    if "FLOR" in key:
        return _title_for_bucket("flor")
    if "FISSUR" in key or "FISUR" in key or "PIT" in key:
        return _title_for_bucket("fissur")
    if "ORTODONTI" in key:
        return _title_for_bucket("ortodonti")
    if "IMPLANT" in key:
        return _title_for_bucket("implant")
    if "EXTIRPASYON" in key:
        return _title_for_bucket("extirpasyon")
    if "DIGER" in key:
        return _title_for_bucket("diger")
    return None


def _card_title_from_api(raw_title):
    """Bilinen kovaya map et; yoksa API'den gelen orijinal basligi koru (coklu 'Diğer' karti olusmasin)."""
    t = _normalize_text(raw_title)
    if not t:
        return ""
    return _map_to_standard_bucket(t) or t


def _ensure_recete_grup_cards(rows):
    """DAGILIMI'de kolonu olmayan reçete gruplari icin bos kart ekler (deger grafikten doldurulur)."""
    rows = list(rows or [])
    titles = {_lookup_key(r.get("title")) for r in rows if r.get("title")}
    for title, gid, category in _RECETE_GRUP_CARD_DEFS:
        if _lookup_key(title) in titles:
            continue
        rows.append({
            "title": title,
            "value": 0,
            "category": category,
            "recete_grup_kodu": gid,
        })
    return _filter_excluded_rows(rows)


def _rows_from_df(df):
    if df is None or df.empty:
        return []

    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]
    title_col = _find_column(df, _TITLE_COLUMNS)
    value_col = _find_column(df, _VALUE_COLUMNS)
    category_col = _find_column(df, _CATEGORY_COLUMNS)
    order_col = _find_column(df, _ORDER_COLUMNS)
    id_col = _find_column(df, ("RECETE_GRUP_ID", "RECETE_GRUP_KODU", "RECETE_GRUP_KOD"))

    if title_col and value_col:
        work = df.copy()
        work[value_col] = work[value_col].apply(_coerce_count)

        grouped = {}
        for _, row in work.iterrows():
            title = _normalize_text(row.get(title_col))
            if not title:
                continue
            display_title = _card_title_from_api(title)
            if not display_title:
                continue
            rec_g = ""
            if id_col:
                try:
                    rec_g = str(int(float(row.get(id_col))))
                except (TypeError, ValueError):
                    rec_g = ""
            if _is_yer_tutucu_card(display_title, rec_g):
                continue
            value = _coerce_count(row.get(value_col))
            category = _normalize_text(row.get(category_col)) if category_col else ""
            if display_title not in grouped:
                grouped[display_title] = {
                    "title": display_title,
                    "value": value,
                    "category": category,
                    "order": _CARD_ORDER.get(display_title, 98),
                    "recete_grup_kodu": rec_g,
                }
            else:
                grouped[display_title]["value"] += value
                grouped[display_title]["recete_grup_kodu"] = _merge_recete_grup_kodu(
                    grouped[display_title].get("recete_grup_kodu"), rec_g
                )
            if category and not grouped[display_title].get("category"):
                grouped[display_title]["category"] = category

        rows = list(grouped.values())
        if order_col and len(rows) == len(work.index):
            rows = sorted(rows, key=lambda item: item.get("order", 98))
        else:
            rows = sorted(rows, key=lambda item: item.get("order", 98))
        for row in rows:
            row["value"] = _coerce_count(row.get("value"))
            row.pop("order", None)
        return _filter_excluded_rows(rows)

    if id_col and value_col:
        grouped = {}
        for _, row in df.iterrows():
            raw = row.get(id_col)
            try:
                gid = int(float(raw))
            except (TypeError, ValueError):
                continue
            label = _RECETE_GRUP_ID_TO_AD.get(gid) or "Diğer"
            display_title = _card_title_from_api(label) or label
            if _is_yer_tutucu_card(display_title, str(gid)):
                continue
            val = _coerce_count(row.get(value_col))
            if display_title not in grouped:
                grouped[display_title] = {
                    "title": display_title,
                    "value": val,
                    "category": "",
                    "order": _CARD_ORDER.get(display_title, 98),
                    "recete_grup_kodu": str(gid),
                }
            else:
                grouped[display_title]["value"] += val
                grouped[display_title]["recete_grup_kodu"] = _merge_recete_grup_kodu(
                    grouped[display_title].get("recete_grup_kodu"), str(gid)
                )
        rows = list(grouped.values())
        rows = sorted(rows, key=lambda item: item.get("order", 98))
        for row in rows:
            row["value"] = _coerce_count(row.get("value"))
            row.pop("order", None)
        return _filter_excluded_rows(rows)

    # API tek satirda her islem grubunu ayri sayisal kolon olarak dondururse destekle.
    numeric_rows = []
    for col in df.columns:
        if not len(df.index):
            continue
        numeric = pd_to_number(df[col].iloc[0])
        if numeric is None:
            continue
        col_norm = str(col).strip().upper()
        col_key = _condense_alnum(str(col))
        # DATA1.. veya bilinen kolon adi (typo dahil) ile esle
        mapped = _WIDE_COLUMN_MAP.get(col_key)
        if mapped:
            title_text, gid = mapped
            rec_g = str(gid)
        elif col_norm in _DATA_COLUMN_TITLES:
            title_text = _DATA_COLUMN_TITLES[col_norm]
            rec_g = _DATA_COLUMN_RECETE_GRUP.get(col_norm, "")
        else:
            title_text = _card_title_from_api(str(col).strip())
            rec_g = ""
        if not rec_g:
            rec_g = _CARD_TITLE_RECETE_GRUP.get(title_text, "")
        if not title_text or _is_yer_tutucu_card(title_text, rec_g):
            continue
        numeric_rows.append({
            "title": title_text,
            "value": _coerce_count(numeric),
            "category": "",
            "recete_grup_kodu": rec_g,
            "_col_key": col_key,
        })
    rows = sorted(
        _finalize_wide_numeric_rows(numeric_rows),
        key=lambda item: _CARD_ORDER.get(item["title"], 98),
    )
    return _filter_excluded_rows(_apply_wide_detail_from_df(df, rows))


def _apply_wide_detail_from_df(df, rows):
    """DAGILIMI'de ORTODONTI detay kolonlarini topla."""
    if df is None or df.empty or not len(df.index):
        return list(rows or [])
    rows = list(rows or [])
    by_key = {_title_key(r.get("title")): r for r in rows if r.get("title")}
    title_by_key = {_title_key(t): t for t in _CARD_ORDER.keys()}

    for title_key, rules in _WIDE_COLUMN_PRIORITY.items():
        detail_cols = rules.get("detail") or frozenset()
        if not detail_cols:
            continue
        detail_sum = 0
        found = False
        for col in df.columns:
            col_key = _condense_alnum(str(col))
            if col_key in rules.get("aggregate", frozenset()) or col_key not in detail_cols:
                continue
            numeric = pd_to_number(df[col].iloc[0])
            if numeric is None:
                continue
            detail_sum += _coerce_count(numeric)
            found = True
        if not found or detail_sum <= 0:
            continue
        canonical = title_by_key.get(title_key) or next(
            (r.get("title") for r in rows if _title_key(r.get("title")) == title_key), ""
        )
        if not canonical:
            continue
        rec_g = _CARD_TITLE_RECETE_GRUP.get(canonical, "")
        if title_key in by_key:
            by_key[title_key]["value"] = detail_sum
            if rec_g:
                by_key[title_key]["recete_grup_kodu"] = rec_g
        else:
            rows.append({
                "title": canonical,
                "value": detail_sum,
                "category": "",
                "recete_grup_kodu": rec_g,
            })
    return rows


# Ay isimleri UTF-8 JSON'dan geliyor; sunucuda .py dosyasi ANSI okunsa bile bozulmaz.
_MONTH_NAMES_TR = tuple(_TR["month_names_tr"])
_MONTH_NAME_TO_NUM = {}
for _idx, _name in enumerate(_MONTH_NAMES_TR, start=1):
    _MONTH_NAME_TO_NUM[_condense_alnum(_name)] = _idx
# ASCII karsiliklarini da ekle (SUBAT, AGUSTOS vb.)
for _ascii, _num in (
    ("OCAK", 1), ("SUBAT", 2), ("MART", 3), ("NISAN", 4), ("MAYIS", 5),
    ("HAZIRAN", 6), ("TEMMUZ", 7), ("AGUSTOS", 8), ("EYLUL", 9),
    ("EKIM", 10), ("KASIM", 11), ("ARALIK", 12),
):
    _MONTH_NAME_TO_NUM.setdefault(_ascii, _num)


def _month_num_from_label(label):
    """'Mart 2026', 'MART2026', 'Mayis' -> ay numarasi (1-12)."""
    key = _condense_alnum(label)
    if key in _MONTH_NAME_TO_NUM:
        return _MONTH_NAME_TO_NUM[key]
    for name, num in sorted(_MONTH_NAME_TO_NUM.items(), key=lambda x: -len(x[0])):
        if key.startswith(name) or name in key:
            return num
    return None


def _year_from_label(label, default_year):
    for part in str(label or "").replace(",", " ").split():
        if part.isdigit() and len(part) == 4:
            return int(part)
    return default_year


def _align_series_to_graph_window(labels, values, graph_end_str, month_count=6):
    """Grafikte eksik aylari 0 ile doldurur (6 aylik pencere)."""
    ed = _parse_iso_date(graph_end_str)
    if not ed:
        return labels or [], values or []

    by_ym = {}
    for lbl, val in zip(labels or [], values or []):
        m = _month_num_from_label(lbl)
        if not m:
            continue
        y = _year_from_label(lbl, ed.year)
        by_ym[(y, m)] = by_ym.get((y, m), 0) + _coerce_count(val)

    out_labels, out_values = [], []
    for start, _, lbl in _month_ranges(ed, month_count):
        out_labels.append(lbl)
        out_values.append(by_ym.get((start.year, start.month), 0))
    return out_labels, out_values


def _infer_graph_columns(df):
    month_col = _find_column(
        df,
        ("AYADI", "AY_ADI", "AY", "AY_NAME", "TUR_DEGER", "TUR_DEĞER"),
    )
    value_col = _find_column(
        df,
        ("HIZMET_SAYISI", "HİZMET_SAYISI", "ADET", "SAYI", "TOPLAM", "MIKTAR", "MİKTAR"),
    )
    if month_col and value_col:
        return month_col, value_col, _find_column(df, ("TUR_DETAY_SIRA", "AYKODU", "AY_KODU"))

    sira_col = _find_column(df, ("TUR_DETAY_SIRA", "AYKODU", "AY_KODU", "AY_SIRA"))
    value_col = value_col or None
    month_col = month_col or None

    if value_col is None:
        for col in df.columns:
            sample = df[col].iloc[0] if len(df.index) else None
            if pd_to_number(sample) is not None:
                value_col = col
                break

    if month_col is None:
        for col in df.columns:
            if col == value_col:
                continue
            sample = df[col].iloc[0] if len(df.index) else None
            if pd_to_number(sample) is None:
                month_col = col
                break

    return month_col, value_col, sira_col


def _label_from_month_sira(sira, sd, ed):
    """TUR_DETAY_SIRA (1-12) -> 'Mayis 2026' (Ayadi NULL geldiginde)."""
    try:
        m = int(float(sira))
    except (TypeError, ValueError):
        return ""
    if m < 1 or m > 12:
        return ""
    if sd and ed:
        for start, _, _ in _month_ranges(ed, 24):
            if start.month == m and sd <= start <= ed:
                return f"{_MONTH_NAMES_TR[m - 1]} {start.year}"
    return _MONTH_NAMES_TR[m - 1]


def _graph_series_from_df(df, start_date=None, end_date=None):
    if df is None or df.empty:
        return [], []

    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]
    month_col, value_col, sira_col = _infer_graph_columns(df)

    if not value_col:
        return [], []

    sd = _parse_iso_date(start_date) if start_date else None
    ed = _parse_iso_date(end_date) if end_date else None

    items = []
    for _, row in df.iterrows():
        label = _normalize_text(row.get(month_col)) if month_col else ""
        if not label and sira_col:
            label = _label_from_month_sira(row.get(sira_col), sd, ed)
        if not label and month_col is None and sira_col is None:
            # Tek sayisal ay kolonu (1-12) veya satir sirasi
            for col in df.columns:
                ckey = _condense_alnum(col)
                if ckey in _MONTH_NAME_TO_NUM:
                    label = str(col).strip()
                    break
        value = pd_to_number(row.get(value_col))
        if not label or value is None:
            continue
        # Sadece ay numarasi geldiyse (or. "5") etiketi tamamla
        if label.isdigit():
            label = _label_from_month_sira(label, sd, ed) or label
        items.append((label, int(round(value))))

    if not items:
        return [], []

    # API "TUR_DETAY_SIRA" (1-12) ile siraladigi icin yil sinirini asan araliklarda
    # kronolojik yerine takvim ayi sirasi gelir. Yili atayip kronolojik siralayalim.
    if start_date and end_date:
        sd = _parse_iso_date(start_date)
        ed = _parse_iso_date(end_date)
        if sd and ed:
            sorted_items = _chronological_sort(items, sd, ed)
            if sorted_items:
                items = sorted_items

    labels = [a for a, _ in items]
    values = [b for _, b in items]
    return labels, values


def _parse_iso_date(value):
    try:
        if isinstance(value, date):
            return value
        from datetime import datetime
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _chronological_sort(items, sd, ed):
    """Etiketleri (ay adi) sd-ed araligindaki yil bilgisiyle kronolojik siralar."""
    expected = []
    cur = _month_start(sd)
    last = _month_start(ed)
    safety = 0
    while cur <= last and safety < 240:
        expected.append((cur.year, cur.month))
        cur = _add_months(cur, 1)
        safety += 1

    seen = {}
    output = []
    for label, val in items:
        m = _month_num_from_label(label)
        if not m:
            return None
        year = None
        # Etiket icin sd-ed icindeki ilk uygun yili sec (mukerrer girilirse ikinciyi vs. degerlendir).
        used = seen.get(m, 0)
        candidates = [y for (y, mm) in expected if mm == m]
        if used < len(candidates):
            year = candidates[used]
            seen[m] = used + 1
        else:
            year = candidates[0] if candidates else sd.year
        output.append(((year, m), label, val))
    output.sort(key=lambda t: t[0])
    return [(lbl, val) for _, lbl, val in output]


def _merge_monthly_series(series_list, graph_start_str, graph_end_str):
    merged = {}
    for labels, values in series_list:
        for label, val in zip(labels or [], values or []):
            merged[label] = merged.get(label, 0) + _coerce_count(val)
    if not merged:
        return [], []
    labels = list(merged.keys())
    values = [merged[k] for k in labels]
    sd = _parse_iso_date(graph_start_str)
    ed = _parse_iso_date(graph_end_str)
    if sd and ed:
        sorted_items = _chronological_sort(list(zip(labels, values)), sd, ed)
        if sorted_items:
            return [a for a, _ in sorted_items], [b for _, b in sorted_items]
    return labels, values


def _grafik_series_for_recete(graph_start_str, graph_end_str, recete_grup_kodu):
    """
    Kart bazli aylik grafik. Serviste virgullu kod (14,25) tek sorguda bos donebilir;
    once her ID ayri cekilir, sonra birlesik denenir.
    """
    gid = str(recete_grup_kodu or "").strip()
    if not gid or not re.fullmatch(r"\d+(?:\s*,\s*\d+)*", gid):
        return [], []

    parts = [p.strip() for p in gid.split(",") if p.strip()]
    collected = []

    if len(parts) > 1:
        gdf = tedavi_gruplari_dagilimi_grafik_yukle(
            graph_start_str, graph_end_str, recete_grup_kodu=gid
        )
        ml, mv = _graph_series_from_df(gdf, graph_start_str, graph_end_str)
        if ml and any(v for v in (mv or [])):
            return _align_series_to_graph_window(ml, mv, graph_end_str)
        for part in parts:
            part_df = tedavi_gruplari_dagilimi_grafik_yukle(
                graph_start_str, graph_end_str, recete_grup_kodu=part
            )
            collected.append(_graph_series_from_df(part_df, graph_start_str, graph_end_str))
        merged = _merge_monthly_series(collected, graph_start_str, graph_end_str)
        if merged[0]:
            return _align_series_to_graph_window(merged[0], merged[1], graph_end_str)
        return [], []

    gdf = tedavi_gruplari_dagilimi_grafik_yukle(graph_start_str, graph_end_str, recete_grup_kodu=gid)
    ml, mv = _graph_series_from_df(gdf, graph_start_str, graph_end_str)
    if ml:
        return _align_series_to_graph_window(ml, mv, graph_end_str)
    if gdf is not None and not gdf.empty:
        print(
            f"[TEDAVI_KARTLARI] grafik satirlari var ama ay serisi bos: "
            f"gid={gid}, kolonlar={list(gdf.columns)}"
        )
    return [], []


def _wide_col_keys_for_title(title):
    """Kart basligina karsilik gelen GRAFIK pivot kolon anahtarlari."""
    keys = list(_CARD_TITLE_WIDE_COL_KEYS.get(title) or [])
    condensed_title = _condense_alnum(title)
    if condensed_title and condensed_title not in keys:
        keys.append(condensed_title)
    return keys


def _find_column_for_keys(df, key_candidates):
    if df is None or df.empty:
        return None
    wanted = {_condense_alnum(k) for k in key_candidates if k}
    for col in df.columns:
        if _condense_alnum(col) in wanted:
            return col
    return None


def _find_value_column_for_card(df, title):
    """Yeni GRAFIK (SUT satirlari): secili kartin sayisal pivot kolonu."""
    if df is None or df.empty or not title:
        return None
    allowed = {_condense_alnum(k) for k in _wide_col_keys_for_title(title)}
    if not allowed:
        return None
    for col in df.columns:
        if _condense_alnum(col) in allowed:
            return col
    return None


def _sut_breakdown_from_grafik_df(df, title):
    """
    GRAFIK SQL SUT pivotu: Hizmet_Kodu, Hizmet_Sut_Tanimi + kart kolonu.
    Donus: [{sut_kodu, sut_tanimi, adet, yuzde}, ...]
    """
    if df is None or df.empty or not title:
        return []

    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]
    kod_col = _find_column_for_keys(df, _SUT_KOD_COLUMNS)
    tanim_col = _find_column_for_keys(df, _SUT_TANIM_COLUMNS)
    value_col = _find_value_column_for_card(df, title)
    if not kod_col or not value_col:
        return []

    rows = []
    for _, row in df.iterrows():
        adet = _coerce_count(row.get(value_col))
        if adet <= 0:
            continue
        kod = _normalize_text(row.get(kod_col)) or "-"
        tanim = _normalize_text(row.get(tanim_col)) if tanim_col else ""
        if not tanim:
            tanim = kod
        rows.append({"sut_kodu": kod, "sut_tanimi": tanim, "adet": adet})

    if not rows:
        return []

    rows.sort(key=lambda item: (-item["adet"], item["sut_kodu"]))
    total = sum(item["adet"] for item in rows)
    if total <= 0:
        return []

    out = []
    for item in rows:
        pct = round(100.0 * item["adet"] / total, 1)
        out.append({
            "sut_kodu": item["sut_kodu"],
            "sut_tanimi": item["sut_tanimi"],
            "adet": item["adet"],
            "yuzde": pct,
        })
    return out


def _iter_calendar_month_slices(period_start_str, period_end_str):
    """Tarih araligini takvim ayi dilimlerine boler (grafik N ay ile uyumlu)."""
    sd = _parse_iso_date(period_start_str)
    ed = _parse_iso_date(period_end_str)
    if not sd or not ed or sd > ed:
        return []
    out = []
    cur = _month_start(sd)
    while cur <= ed:
        month_end = min(_add_months(cur, 1) - timedelta(days=1), ed)
        month_start = max(cur, sd)
        out.append((month_start.strftime("%Y-%m-%d"), month_end.strftime("%Y-%m-%d")))
        cur = _add_months(cur, 1)
    return out


def _card_sut_breakdown(title, recete_grup_kodu, period_start_str, period_end_str):
    """Secili donem + reçete grubu icin SUT kırılım; cok ay seciliyse aylik toplanir."""
    gid = str(recete_grup_kodu or "").strip()
    if not gid or not re.fullmatch(r"\d+(?:\s*,\s*\d+)*", gid):
        return []
    if _is_yer_tutucu_card(title, gid):
        return []

    slices = _iter_calendar_month_slices(period_start_str, period_end_str)
    if not slices:
        return []

    merged = {}
    for m_start, m_end in slices:
        try:
            df = tedavi_gruplari_dagilimi_grafik_yukle(
                m_start, m_end, recete_grup_kodu=gid
            )
        except Exception as exc:
            print(f"[TEDAVI_KARTLARI] SUT kırılım ({m_start}-{m_end}) hata: {exc}")
            continue
        for row in _sut_breakdown_from_grafik_df(df, title):
            key = row.get("sut_kodu") or "-"
            if key not in merged:
                merged[key] = {
                    "sut_kodu": key,
                    "sut_tanimi": row.get("sut_tanimi") or key,
                    "adet": 0,
                }
            merged[key]["adet"] += _coerce_count(row.get("adet"))

    if not merged:
        return []

    rows = sorted(merged.values(), key=lambda item: (-item["adet"], item["sut_kodu"]))
    total = sum(item["adet"] for item in rows)
    if total <= 0:
        return []

    out = []
    for item in rows:
        adet = item["adet"]
        out.append({
            "sut_kodu": item["sut_kodu"],
            "sut_tanimi": item["sut_tanimi"],
            "adet": adet,
            "yuzde": round(100.0 * adet / total, 1),
        })
    return out


def _grafik_period_total(period_start_str, period_end_str, recete_grup_kodu):
    """Secilen tarih araliginda RECETE_GRUP filtresine gore toplam islem sayisi."""
    gid = str(recete_grup_kodu or "").strip()
    if not gid or not re.fullmatch(r"\d+(?:\s*,\s*\d+)*", gid):
        return 0

    parts = [p.strip() for p in gid.split(",") if p.strip()]
    if len(parts) > 1:
        total = 0
        for part in parts:
            total += _grafik_period_total(period_start_str, period_end_str, part)
        return total

    df = tedavi_gruplari_dagilimi_grafik_yukle(
        period_start_str, period_end_str, recete_grup_kodu=gid
    )
    if df is None or df.empty:
        return 0
    # Donem toplami icin ay etiketi zorunlu degil; sadece sayisal kolonu topla.
    # Serviste AYADI bos gelebiliyor, bu durumda _graph_series_from_df satirlari eleyip 0 donduruyordu.
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]
    _month_col, value_col, _sira_col = _infer_graph_columns(df)
    if value_col:
        return _safe_int_sum(df[value_col])
    sd = _parse_iso_date(period_start_str)
    ed = _parse_iso_date(period_end_str)
    _, values = _graph_series_from_df(df, sd, ed)
    return _safe_int_sum(values)


def _monthly_per_card_from_dagilimi(graph_end_str, month_count=6):
    """
    GRAFIK SQL bos donerse: her ay icin DAGILIMI'yi ayri cagirip kart bazli aylik degerleri toplar.
    Donus: ({title: [v_m1, v_m2, ...]}, [label_m1, label_m2, ...])
    """
    ed = _parse_iso_date(graph_end_str)
    if not ed:
        return {}, []

    ranges = _month_ranges(ed, month_count)
    labels = [r[2] for r in ranges]
    per_card = {}

    for idx, (start, end, _label) in enumerate(ranges):
        try:
            df = tedavi_gruplari_dagilimi_yukle(start.isoformat(), end.isoformat())
        except Exception as exc:
            print(f"[TEDAVI_KARTLARI] dagilimi aylik fallback hata: {exc}")
            continue
        rows = _rows_from_df(df)
        for row in rows or []:
            title = row.get("title")
            if not title:
                continue
            if title not in per_card:
                per_card[title] = [0] * month_count
            per_card[title][idx] = int(row.get("value") or 0)

    return per_card, labels


def _json_safe_scalar(value):
    """Flask tojson / jsonify icin numpy ve NaN degerlerini Python tipine cevirir."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, (bool, int, float, str)):
        if isinstance(value, float) and (value != value):  # NaN
            return None
        return value
    try:
        if hasattr(value, "item"):
            return value.item()
    except (TypeError, ValueError):
        pass
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return float(value)
        except (TypeError, ValueError):
            return str(value)


def _json_safe_cards(cards):
    safe = []
    for card in cards or []:
        safe.append(
            {
                "id": str(card.get("id") or ""),
                "title": _display_str(card.get("title") or ""),
                "value": _coerce_count(_json_safe_scalar(card.get("value"))),
                "category": _display_str(card.get("category") or ""),
                "icon": _display_str(card.get("icon") or ""),
                "color": str(card.get("color") or "#475569"),
                "description": _display_str(card.get("description") or ""),
                "recete_grup_kodu": str(card.get("recete_grup_kodu") or ""),
                "monthly_labels": [_display_str(x) for x in (card.get("monthly_labels") or [])],
                "monthly_values": [
                    int(_json_safe_scalar(v) or 0) for v in (card.get("monthly_values") or [])
                ],
            }
        )
    return safe


def _log_tedavi_kartlari_error(exc, context):
    try:
        current_app.logger.exception("[TEDAVI_KARTLARI] %s: %s", context, exc)
    except RuntimeError:
        print(f"[TEDAVI_KARTLARI] {context}: {exc}")


def _resolve_row_gid(row):
    gid = str(row.get("recete_grup_kodu") or "").strip()
    if not gid:
        gid = _CARD_TITLE_RECETE_GRUP.get(row.get("title"), "")
    return gid


def _card_monthly_series(title, gid, graph_start_str, graph_end_str, dagilimi_per_card=None, dagilimi_labels=None):
    """Tek kart icin aylik seri (modal / API). GRAFIK bos ise DAGILIMI aylik fallback."""
    if gid and re.fullmatch(r"\d+(?:\s*,\s*\d+)*", gid):
        ml, mv = _grafik_series_for_recete(graph_start_str, graph_end_str, gid)
    else:
        ml, mv = [], []

    if title and (not ml or not any(v for v in (mv or []))):
        if dagilimi_per_card is None:
            dagilimi_per_card, dagilimi_labels = _monthly_per_card_from_dagilimi(graph_end_str, 6)
        fallback_values = (dagilimi_per_card or {}).get(title)
        if fallback_values and any(v for v in fallback_values):
            ml = dagilimi_labels or []
            mv = fallback_values

    return ml or [], mv or []


def _title_key(title):
    return _condense_alnum(title or "")


def _is_implausible_count(title, value):
    """806090 / 407070 gibi birlestirilmis veya SQL hatali ozet degerleri."""
    value = _coerce_count(value)
    if value <= 0:
        return False
    cap = _MAX_PLAUSIBLE_BY_TITLE.get(_title_key(title))
    if cap is not None and value > cap:
        return True
    text = str(value)
    if len(text) >= 6 and value > 9999:
        return True
    return False


def _sum_series_in_period(labels, values, period_start_str, period_end_str):
    """kart-serisi ile ayni 6 aylik pencereden, secili tarih filtresine dusen aylari topla."""
    sd = _parse_iso_date(period_start_str)
    ed = _parse_iso_date(period_end_str)
    if not sd or not ed:
        return _safe_int_sum(values)
    total = 0
    for lbl, val in zip(labels or [], values or []):
        m = _month_num_from_label(lbl)
        if not m:
            continue
        y = _year_from_label(lbl, ed.year)
        month_start = date(y, m, 1)
        month_end = _add_months(month_start, 1) - timedelta(days=1)
        if month_end >= sd and month_start <= ed:
            total += _coerce_count(val)
    return total


def _grafik_period_total_for_card(title, period_start_str, period_end_str, gid):
    """Popup ile ayni: 6 aylik grafik SQL + secilen donemdeki aylar (Bu Ay = tek ay 38)."""
    ed = _parse_iso_date(period_end_str)
    if not ed:
        return 0
    graph_start_str = _graph_month_start(ed, 6).strftime("%Y-%m-%d")
    ml, mv = _grafik_series_for_recete(graph_start_str, period_end_str, gid)
    total = _sum_series_in_period(ml, mv, period_start_str, period_end_str)
    if total > 0 and not _is_implausible_count(title, total):
        return total
    return 0


def _card_period_value(row, gid, period_start_str, period_end_str):
    """Ortodonti vb.: DAGILIMI ozetine guvenme; grafik SQL toplamini kullan."""
    title = row.get("title") or ""
    card_value = _coerce_count(row.get("value"))
    has_gid = bool(gid and re.fullmatch(r"\d+(?:\s*,\s*\d+)*", gid))
    if not has_gid or not period_start_str or not period_end_str:
        return card_value

    tk = _title_key(title)
    force_grafik = (
        tk in _FORCE_GRAFIK_TITLE_KEYS
        or title in _CARD_PERIOD_VALUE_FROM_GRAFIK
    )
    implausible = _is_implausible_count(title, card_value)

    if card_value > 0 and not force_grafik and not implausible:
        return card_value

    period_total = _grafik_period_total_for_card(
        title, period_start_str, period_end_str, gid
    )
    if period_total > 0:
        if card_value != period_total:
            try:
                current_app.logger.info(
                    "[TEDAVI_KARTLARI] '%s' DAGILIMI=%s -> GRAFIK=%s (gid=%s)",
                    title, card_value, period_total, gid,
                )
            except RuntimeError:
                pass
        return period_total

    if card_value > 0 and not implausible:
        return card_value
    if implausible or force_grafik:
        return 0
    return card_value


def _build_cards_fast(
    current_rows,
    period_start_str=None,
    period_end_str=None,
    defer_grafik_period=False,
):
    """
    Sayfa acilisinda yalnizca ozet dagilim (defer_grafik_period=True).
    GRAFIK ile duzeltilen kartlar /kart-degerleri ile arka planda guncellenir.
    Aylik grafik modal acilinca /kart-serisi ile yuklenir.
    """
    current_rows = _filter_excluded_rows(
        sorted(current_rows or [], key=lambda row: _CARD_ORDER.get(row["title"], 98))
    )
    cards = []
    for index, row in enumerate(current_rows):
        category, color, description = _card_meta_for(row["title"], row.get("category"))
        if not row.get("category"):
            row["category"] = category
        display_category = _display_str(row.get("category") or category or "Diğer") or "Diğer"
        icon = _card_icon_letter(row.get("title"), display_category)
        gid = _resolve_row_gid(row)
        if defer_grafik_period:
            card_value = _coerce_count(row.get("value"))
            if _is_implausible_count(row.get("title"), card_value):
                card_value = 0
        else:
            card_value = _card_period_value(row, gid, period_start_str, period_end_str)

        cards.append(
            {
                "id": f"tcard-{index}",
                "title": _display_str(row["title"]),
                "value": card_value,
                "category": display_category,
                "icon": icon,
                "color": color if color != "#475569" else _FALLBACK_COLORS[index % len(_FALLBACK_COLORS)],
                "description": description,
                "recete_grup_kodu": gid,
                "monthly_labels": [],
                "monthly_values": [],
            }
        )
    return cards


def _kart_grid_period_total(title, gid, end_date, months=1):
    """
    Kart izgarasi ve /kart-degerleri: modal (kart-serisi) ile ayni period_total.
    Sayfa filtresi genis olsa bile varsayilan 1 aylik grafik penceresi kullanilir.
    """
    if not gid or _is_yer_tutucu_card(title, gid):
        return 0
    ed = end_date if isinstance(end_date, date) else _parse_iso_date(end_date)
    if not ed:
        return 0
    ed_str = ed.strftime("%Y-%m-%d")
    graph_start_str = _graph_month_start(ed, 6).strftime("%Y-%m-%d")
    bd_start, bd_end = _period_for_chart_months(ed, months, clip_start=None, clip_end=ed)
    if not bd_start or not bd_end:
        return 0
    labels, values = _card_monthly_series(title, gid, graph_start_str, ed_str)
    return _sum_series_in_period(labels, values, bd_start, bd_end)


def _deferred_grafik_card_updates(end_date, months=1):
    """
    card_period_from_grafik kartlari icin modal ile ayni toplami hesaplar (sirali).
    """
    titles = sorted(_CARD_PERIOD_VALUE_FROM_GRAFIK, key=lambda t: _CARD_ORDER.get(t, 98))
    updates = []
    for title in titles:
        gid = _CARD_TITLE_RECETE_GRUP.get(title, "")
        try:
            value = _kart_grid_period_total(title, gid, end_date, months=months)
        except Exception as exc:
            _log_tedavi_kartlari_error(exc, f"kart-degerleri ({title})")
            value = 0
        updates.append({
            "title": title,
            "recete_grup_kodu": gid,
            "value": int(_coerce_count(value)),
        })
    return updates


@tedavi_kartlari_bp.route('/tedavi-kartlari')
@login_required
def tedavi_kartlari():
    sd, ed = get_date_range()
    sd_str = sd.strftime("%Y-%m-%d")
    ed_str = ed.strftime("%Y-%m-%d")

    try:
        current_df = tedavi_gruplari_dagilimi_yukle(sd_str, ed_str)
        try:
            cols = list(current_df.columns) if current_df is not None else []
            head = (
                current_df.head(3).to_dict(orient="records")
                if current_df is not None and not current_df.empty
                else []
            )
            current_app.logger.info(
                "[TEDAVI_KARTLARI] DAGILIMI kolonlar=%s ornek=%s",
                cols, head,
            )
        except Exception:
            pass
        current_rows = _ensure_recete_grup_cards(_rows_from_df(current_df))
        try:
            current_app.logger.info("[TEDAVI_KARTLARI] build=%s", TEDAVI_KARTLARI_BUILD)
        except RuntimeError:
            pass
        treatment_cards = _json_safe_cards(
            _build_cards_fast(
                current_rows,
                period_start_str=sd_str,
                period_end_str=ed_str,
                defer_grafik_period=True,
            )
        )
    except Exception as exc:
        _log_tedavi_kartlari_error(exc, "sayfa verisi")
        treatment_cards = []

    return render_template(
        'tedavi_kartlari.html',
        start_date=sd,
        end_date=ed,
        treatment_cards=treatment_cards,
        ui=TEDAVI_KARTLARI_UI,
        no_data=not bool(treatment_cards),
        page_sql_kodlari=PAGE_SQL_KODLARI,
        deploy_build=TEDAVI_KARTLARI_BUILD,
    )


@tedavi_kartlari_bp.route('/tedavi-kartlari/kart-degerleri')
@login_required
def tedavi_kartlari_kart_degerleri():
    """Sayfa acilisindan sonra GRAFIK ile duzeltilmesi gereken kart sayilarini dondurur."""
    _sd, ed = get_date_range()
    months = request.args.get("months", type=int) or 1
    months = max(1, min(months, 6))

    try:
        updates = _deferred_grafik_card_updates(ed, months=months)
    except Exception as exc:
        _log_tedavi_kartlari_error(exc, "kart-degerleri")
        updates = []

    return jsonify({"updates": updates})


@tedavi_kartlari_bp.route('/tedavi-kartlari/kart-serisi')
@login_required
def tedavi_kartlari_kart_serisi():
    """Modal grafik: secili kartin aylik serisini tek istekte dondurur."""
    sd, ed = get_date_range()
    ed_str = ed.strftime("%Y-%m-%d")
    graph_start_str = _graph_month_start(ed, 6).strftime("%Y-%m-%d")

    title = (request.args.get("title") or "").strip()
    gid = (request.args.get("recete_grup_kodu") or "").strip()
    if not gid and title:
        gid = _CARD_TITLE_RECETE_GRUP.get(title, "")
    if _is_yer_tutucu_card(title, gid):
        return jsonify({"labels": [], "values": [], "period_total": 0, "breakdown": []})

    sd_str = sd.strftime("%Y-%m-%d")
    months = request.args.get("months", type=int) or 1
    months = max(1, min(months, 6))
    breakdown_only = (request.args.get("breakdown_only") or "").strip().lower() in (
        "1", "true", "yes",
    )
    # Modal grafik 6 aylik pencereden kesilir; sayfa "bu ay" filtresi kirilimi tek aya dusurmesin.
    bd_start, bd_end = _period_for_chart_months(ed, months, clip_start=None, clip_end=ed)

    try:
        if breakdown_only:
            breakdown = (
                _card_sut_breakdown(title, gid, bd_start, bd_end)
                if gid and bd_start and bd_end
                else []
            )
            return jsonify({"breakdown": breakdown, "months": months})

        labels, values = _card_monthly_series(title, gid, graph_start_str, ed_str)
        period_total = 0
        if gid and bd_start and bd_end:
            period_total = _sum_series_in_period(labels, values, bd_start, bd_end)
        breakdown = (
            _card_sut_breakdown(title, gid, bd_start, bd_end)
            if gid and bd_start and bd_end
            else []
        )
        payload = {
            "labels": [str(x) for x in (labels or [])],
            "values": [int(_json_safe_scalar(v) or 0) for v in (values or [])],
            "period_total": int(period_total or 0),
            "breakdown": breakdown,
            "months": months,
        }
    except Exception as exc:
        _log_tedavi_kartlari_error(exc, "kart-serisi")
        payload = {"labels": [], "values": [], "breakdown": [], "months": months}

    return jsonify(payload)
