from flask import Blueprint, jsonify, render_template, request
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required  # noqa: E402
from routes.dashboard import get_date_range  # noqa: E402
from database.cari_sorusturma_sorgular import (  # noqa: E402
    cari_firma_ara,
    cari_hareketleri_yukle,
    banka_fis_detay_yukle,
    cari_finans_detay_yukle,
    kasa_fis_detay_yukle,
    alis_fatura_detay_yukle,
)

cari_sorusturma_bp = Blueprint("cari_sorusturma", __name__)

PAGE_SQL_KODLARI = [
    "cari_sorusturma.cari_firma_ara",
    "cari_sorusturma.cari_hareketleri_yukle",
    "cari_sorusturma.banka_cari_fis",
    "cari_sorusturma.banka_cari_fis_hareket",
    "cari_sorusturma.cari_finans",
    "cari_sorusturma.cari_finans_detay",
    "cari_sorusturma.kasa_cari_fis",
    "cari_sorusturma.alis_faturasi_master",
    "cari_sorusturma.alis_faturasi_detay",
]

_MIN_ARAMA_UZUNLUK = 2


@cari_sorusturma_bp.route("/cari-sorusturma/ara")
@login_required
def cari_firma_ara_api():
    arama = (request.args.get("q") or request.args.get("arama") or "").strip()
    if len(arama) < _MIN_ARAMA_UZUNLUK:
        return jsonify(
            {
                "cariler": [],
                "count": 0,
                "min_length": _MIN_ARAMA_UZUNLUK,
            }
        )

    sd, ed = get_date_range()
    start_str = sd.strftime("%Y-%m-%d")
    end_str = ed.strftime("%Y-%m-%d")
    cariler = cari_firma_ara(arama, start_str, end_str)
    return jsonify(
        {
            "cariler": cariler,
            "count": len(cariler),
            "q": arama,
            "start_date": start_str,
            "end_date": end_str,
        }
    )


@cari_sorusturma_bp.route("/cari-sorusturma/hareketler")
@login_required
def cari_hareketleri_api():
    # Hareket sorgusu cari'yi ic ID (CARI_KART_ID) ile filtreler.
    cari_id = (
        request.args.get("cari_id") or request.args.get("cari_kod") or ""
    ).strip()
    if not cari_id:
        return jsonify({"hareketler": [], "count": 0, "error": "cari_id gerekli"}), 400

    sd, ed = get_date_range()
    start_str = sd.strftime("%Y-%m-%d")
    end_str = ed.strftime("%Y-%m-%d")
    hareketler = cari_hareketleri_yukle(cari_id, start_str, end_str)
    return jsonify(
        {
            "hareketler": hareketler,
            "count": len(hareketler),
            "cari_id": cari_id,
            "start_date": start_str,
            "end_date": end_str,
        }
    )


@cari_sorusturma_bp.route("/cari-sorusturma/banka-fis")
@login_required
def banka_fis_detay_api():
    banka_fis_hareket_id = (
        request.args.get("banka_fis_hareket_id")
        or request.args.get("finans_detay_id")
        or ""
    ).strip()
    islem_id = (
        request.args.get("islem_id")
        or request.args.get("bf_hareket_islem_id")
        or ""
    ).strip()
    cari_finans_detay_id = (
        request.args.get("cari_finans_detay_id")
        or request.args.get("finans_detay_id")
        or ""
    ).strip()
    cari_kart_id = (request.args.get("cari_id") or "").strip()
    if not banka_fis_hareket_id and not islem_id and not cari_finans_detay_id:
        return jsonify(
            {
                "fis": None,
                "hareketler": [],
                "count": 0,
                "error": "islem_id veya cari_finans_detay_id gerekli",
            }
        ), 400

    data = banka_fis_detay_yukle(
        banka_fis_hareket_id,
        islem_id,
        cari_finans_detay_id,
        cari_kart_id,
    )
    return jsonify(data)


@cari_sorusturma_bp.route("/cari-sorusturma/cari-finans")
@login_required
def cari_finans_detay_api():
    cari_finans_id = (
        request.args.get("cari_finans_id")
        or request.args.get("islem_id")
        or ""
    ).strip()
    hareket_tur_id = (
        request.args.get("hareket_tur_id")
        or request.args.get("haret_tur_id")
        or ""
    ).strip()
    if not cari_finans_id:
        return jsonify(
            {
                "fis": None,
                "hareketler": [],
                "count": 0,
                "error": "cari_finans_id gerekli",
            }
        ), 400

    data = cari_finans_detay_yukle(cari_finans_id, hareket_tur_id)
    return jsonify(data)


@cari_sorusturma_bp.route("/cari-sorusturma/kasa-fis")
@login_required
def kasa_fis_detay_api():
    kasa_hareket_id = (
        request.args.get("kasa_hareket_id")
        or request.args.get("islem_id")
        or ""
    ).strip()
    if not kasa_hareket_id:
        return jsonify(
            {
                "fis": None,
                "count": 0,
                "error": "kasa_hareket_id gerekli",
            }
        ), 400

    data = kasa_fis_detay_yukle(kasa_hareket_id)
    return jsonify(data)


@cari_sorusturma_bp.route("/cari-sorusturma/alis-fatura")
@login_required
def alis_fatura_detay_api():
    fis_id = (
        request.args.get("fis_id")
        or request.args.get("stok_fs_id")
        or request.args.get("islem_id")
        or ""
    ).strip()
    if not fis_id:
        return jsonify(
            {
                "fis": None,
                "satirlar": [],
                "count": 0,
                "error": "fis_id gerekli",
            }
        ), 400

    data = alis_fatura_detay_yukle(fis_id)
    return jsonify(data)


@cari_sorusturma_bp.route("/cari-sorusturma")
@login_required
def cari_sorusturma():
    sd, ed = get_date_range()
    return render_template(
        "cari_sorusturma.html",
        start_date=sd,
        end_date=ed,
        page_sql_kodlari=PAGE_SQL_KODLARI,
    )
