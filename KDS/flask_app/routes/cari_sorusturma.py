from flask import Blueprint, render_template
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required  # noqa: E402
from routes.dashboard import get_date_range  # noqa: E402

cari_sorusturma_bp = Blueprint("cari_sorusturma", __name__)

PAGE_SQL_KODLARI = []

_ORNEK_CARI_KOD = "201702170001"
_ORNEK_CARI_UNVAN = "METASOFT BİLGİSAYAR BİLGİ İŞLEM HİZMETLERİ LTD. ŞTİ."

# Gecici ornek veri — SQL baglantisi sonraki asamada kaldirilacak
_ORNEK_HAREKETLER = [
    {
        "modul": "Satınalma",
        "tarih": "11.02.2026",
        "fatura_no": "FT12026000000006",
        "belge_no": "1989",
        "belge_tarihi": "",
        "vade_tarihi": "",
        "aciklama": "FT12026000000006 NOLU FATURA",
        "islem_turu": "Alış Faturası",
        "ba": "A",
        "tutar": 144000.0,
        "bakiye": "144.000,00 (A)",
        "doviz_tutar": "",
        "para_birim": "TL",
        "birim_adi": "AKPINAR KERESTE MERKEZ İŞYERİ",
        "ozel_kod": "",
        "odeme_turu": "AÇIK HESAP",
    },
    {
        "modul": "Banka",
        "tarih": "20.02.2026",
        "fatura_no": "",
        "belge_no": "382577234",
        "belge_tarihi": "",
        "vade_tarihi": "",
        "aciklama": "METASOFT EFT",
        "islem_turu": "Banka Gönderilen Havale Fişi",
        "ba": "B",
        "tutar": 144000.0,
        "bakiye": "0",
        "doviz_tutar": "",
        "para_birim": "TL",
        "birim_adi": "AKPINAR KERESTE MERKEZ İŞYERİ",
        "ozel_kod": "",
        "odeme_turu": "",
    },
    {
        "modul": "Cari",
        "tarih": "02.04.2026",
        "fatura_no": "FT02026000000011",
        "belge_no": "FT02026000000011",
        "belge_tarihi": "",
        "vade_tarihi": "02.04.2026",
        "aciklama": "FT02026000000011 NOLU FATURA ESET ANTI...",
        "islem_turu": "Alış Hizmet Faturası",
        "ba": "A",
        "tutar": 40353.68,
        "bakiye": "40.353,68 (A)",
        "doviz_tutar": "",
        "para_birim": "TL",
        "birim_adi": "AKPINAR KERESTE MERKEZ İŞYERİ",
        "ozel_kod": "",
        "odeme_turu": "",
    },
    {
        "modul": "Banka",
        "tarih": "06.04.2026",
        "fatura_no": "",
        "belge_no": "F24474",
        "belge_tarihi": "",
        "vade_tarihi": "",
        "aciklama": "METASOFT EFT",
        "islem_turu": "Banka Gönderilen Havale Fişi",
        "ba": "B",
        "tutar": 40353.68,
        "bakiye": "0",
        "doviz_tutar": "",
        "para_birim": "TL",
        "birim_adi": "AKPINAR KERESTE MERKEZ İŞYERİ",
        "ozel_kod": "",
        "odeme_turu": "",
    },
]


@cari_sorusturma_bp.route("/cari-sorusturma")
@login_required
def cari_sorusturma():
    sd, ed = get_date_range()

    # SQL entegrasyonu sonraki asamada: cari secimi ve sorgu eklenecek
    return render_template(
        "cari_sorusturma.html",
        start_date=sd,
        end_date=ed,
        cari_kod=_ORNEK_CARI_KOD,
        cari_unvan=_ORNEK_CARI_UNVAN,
        hareketler=_ORNEK_HAREKETLER,
        page_sql_kodlari=PAGE_SQL_KODLARI,
    )
