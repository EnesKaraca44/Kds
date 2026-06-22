from flask import Blueprint, render_template
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required
from routes.dashboard import get_date_range

stok_durum_bp = Blueprint('stok_durum', __name__)

PAGE_SQL_KODLARI = [
    "local:Bu sayfada henüz rapor API çağrısı yok (örnek arayüz; canlı SQL bağlantısı sonra eklenecek).",
]

# Örnek veri — SQL bağlandığında kaldırılacak
ORNEK_SATIRLAR = [
    {
        "hareket_turu": "Satınalma",
        "malzeme_kodu": "150.01.05.01.03",
        "malzeme_adi": "A4 KAĞIT",
        "malzeme_aciklama": "A4 KAĞIT",
        "birim": "KOLİ",
        "giris": 120,
        "cikis": 45,
        "mevcut": 75,
        "minimum": 20,
        "kritik": 10,
        "maximum": 200,
        "yillik": 180,
        "stok_fazlasi": 0,
        "son_kullanim": "",
        "seri_lot": "",
    },
    {
        "hareket_turu": "Devir",
        "malzeme_kodu": "150.01.05.02.01",
        "malzeme_adi": "ZIMBA TELİ 24/6 10 LU KUTU",
        "malzeme_aciklama": "ZIMBA TELİ 24/6 10 LU KUTU",
        "birim": "ADET",
        "giris": 50,
        "cikis": 12,
        "mevcut": 38,
        "minimum": 15,
        "kritik": 5,
        "maximum": 100,
        "yillik": 60,
        "stok_fazlasi": 0,
        "son_kullanim": "",
        "seri_lot": "LOT-2024-001",
    },
    {
        "hareket_turu": "Satınalma",
        "malzeme_kodu": "150.01.05.03.02",
        "malzeme_adi": "MASAÜSTÜ KALEM MAVİ",
        "malzeme_aciklama": "MASAÜSTÜ KALEM MAVİ",
        "birim": "ADET",
        "giris": 200,
        "cikis": 85,
        "mevcut": 115,
        "minimum": 50,
        "kritik": 20,
        "maximum": 300,
        "yillik": 240,
        "stok_fazlasi": 0,
        "son_kullanim": "",
        "seri_lot": "",
    },
    {
        "hareket_turu": "Devir",
        "malzeme_kodu": "150.02.01.01.01",
        "malzeme_adi": "ELDİVEN NİTRİL M",
        "malzeme_aciklama": "ELDİVEN NİTRİL M",
        "birim": "PAKET",
        "giris": 80,
        "cikis": 62,
        "mevcut": 18,
        "minimum": 30,
        "kritik": 15,
        "maximum": 150,
        "yillik": 200,
        "stok_fazlasi": 0,
        "son_kullanim": "15.06.2026",
        "seri_lot": "SN-88421",
    },
    {
        "hareket_turu": "Satınalma",
        "malzeme_kodu": "150.02.01.02.03",
        "malzeme_adi": "CERRAHİ MASKE 3 KATLI",
        "malzeme_aciklama": "CERRAHİ MASKE 3 KATLI",
        "birim": "PAKET",
        "giris": 150,
        "cikis": 98,
        "mevcut": 52,
        "minimum": 40,
        "kritik": 20,
        "maximum": 200,
        "yillik": 300,
        "stok_fazlasi": 0,
        "son_kullanim": "01.12.2027",
        "seri_lot": "LOT-M-5521",
    },
    {
        "hareket_turu": "Devir",
        "malzeme_kodu": "150.03.01.01.05",
        "malzeme_adi": "DEZENFEKTAN 1 LT",
        "malzeme_aciklama": "DEZENFEKTAN 1 LT",
        "birim": "ADET",
        "giris": 60,
        "cikis": 48,
        "mevcut": 12,
        "minimum": 25,
        "kritik": 10,
        "maximum": 80,
        "yillik": 96,
        "stok_fazlasi": 0,
        "son_kullanim": "30.09.2026",
        "seri_lot": "LOT-DZ-102",
    },
    {
        "hareket_turu": "Satınalma",
        "malzeme_kodu": "150.03.02.01.01",
        "malzeme_adi": "STERİL GAUZE 10x10",
        "malzeme_aciklama": "STERİL GAUZE 10x10",
        "birim": "PAKET",
        "giris": 300,
        "cikis": 210,
        "mevcut": 90,
        "minimum": 60,
        "kritik": 30,
        "maximum": 400,
        "yillik": 500,
        "stok_fazlasi": 0,
        "son_kullanim": "20.03.2028",
        "seri_lot": "LOT-GZ-778",
    },
    {
        "hareket_turu": "Devir",
        "malzeme_kodu": "150.04.01.02.04",
        "malzeme_adi": "ENJEKTÖR 5 ML",
        "malzeme_aciklama": "ENJEKTÖR 5 ML",
        "birim": "ADET",
        "giris": 500,
        "cikis": 420,
        "mevcut": 80,
        "minimum": 100,
        "kritik": 50,
        "maximum": 600,
        "yillik": 800,
        "stok_fazlasi": 0,
        "son_kullanim": "10.01.2027",
        "seri_lot": "SN-EJ-3344",
    },
    {
        "hareket_turu": "Satınalma",
        "malzeme_kodu": "150.04.02.01.02",
        "malzeme_adi": "KANÜL 22G",
        "malzeme_aciklama": "KANÜL 22G",
        "birim": "ADET",
        "giris": 400,
        "cikis": 310,
        "mevcut": 90,
        "minimum": 80,
        "kritik": 40,
        "maximum": 500,
        "yillik": 600,
        "stok_fazlasi": 0,
        "son_kullanim": "05.08.2027",
        "seri_lot": "LOT-KN-991",
    },
    {
        "hareket_turu": "Devir",
        "malzeme_kodu": "150.05.01.01.01",
        "malzeme_adi": "DENTAL KOMPOZİT A2",
        "malzeme_aciklama": "DENTAL KOMPOZİT A2",
        "birim": "ADET",
        "giris": 25,
        "cikis": 18,
        "mevcut": 7,
        "minimum": 10,
        "kritik": 5,
        "maximum": 40,
        "yillik": 30,
        "stok_fazlasi": 0,
        "son_kullanim": "22.11.2026",
        "seri_lot": "LOT-DC-A2",
    },
    {
        "hareket_turu": "Satınalma",
        "malzeme_kodu": "150.05.02.03.01",
        "malzeme_adi": "DENTAL BONDING AJANI",
        "malzeme_aciklama": "DENTAL BONDING AJANI",
        "birim": "ADET",
        "giris": 30,
        "cikis": 22,
        "mevcut": 8,
        "minimum": 12,
        "kritik": 6,
        "maximum": 50,
        "yillik": 36,
        "stok_fazlasi": 0,
        "son_kullanim": "14.04.2027",
        "seri_lot": "SN-BD-2201",
    },
    {
        "hareket_turu": "Devir",
        "malzeme_kodu": "150.06.01.01.02",
        "malzeme_adi": "DİŞ İPLİĞİ 50M",
        "malzeme_aciklama": "DİŞ İPLİĞİ 50M",
        "birim": "ADET",
        "giris": 100,
        "cikis": 55,
        "mevcut": 45,
        "minimum": 30,
        "kritik": 15,
        "maximum": 120,
        "yillik": 90,
        "stok_fazlasi": 0,
        "son_kullanim": "",
        "seri_lot": "",
    },
    {
        "hareket_turu": "Satınalma",
        "malzeme_kodu": "150.06.02.01.04",
        "malzeme_adi": "AĞIZ GARGARASI 250 ML",
        "malzeme_aciklama": "AĞIZ GARGARASI 250 ML",
        "birim": "ADET",
        "giris": 70,
        "cikis": 40,
        "mevcut": 30,
        "minimum": 25,
        "kritik": 10,
        "maximum": 100,
        "yillik": 80,
        "stok_fazlasi": 0,
        "son_kullanim": "18.07.2027",
        "seri_lot": "LOT-AG-445",
    },
    {
        "hareket_turu": "Devir",
        "malzeme_kodu": "150.07.01.02.01",
        "malzeme_adi": "ALGİNAT ÖLÇÜ MATERYALİ",
        "malzeme_aciklama": "ALGİNAT ÖLÇÜ MATERYALİ",
        "birim": "PAKET",
        "giris": 40,
        "cikis": 28,
        "mevcut": 12,
        "minimum": 15,
        "kritik": 8,
        "maximum": 60,
        "yillik": 48,
        "stok_fazlasi": 0,
        "son_kullanim": "03.02.2027",
        "seri_lot": "LOT-AL-332",
    },
    {
        "hareket_turu": "Satınalma",
        "malzeme_kodu": "150.07.02.01.03",
        "malzeme_adi": "DİŞ FIRÇASI YETİŞKİN",
        "malzeme_aciklama": "DİŞ FIRÇASI YETİŞKİN",
        "birim": "ADET",
        "giris": 250,
        "cikis": 180,
        "mevcut": 70,
        "minimum": 50,
        "kritik": 25,
        "maximum": 300,
        "yillik": 280,
        "stok_fazlasi": 0,
        "son_kullanim": "",
        "seri_lot": "",
    },
]


def _stok_durum_hesapla(row: dict) -> str:
    mevcut = float(row.get('mevcut') or 0)
    kritik = float(row.get('kritik') or 0)
    minimum = float(row.get('minimum') or 0)
    if mevcut <= kritik or mevcut <= 0:
        return 'Kritik'
    if mevcut <= minimum:
        return 'Tedarik Edilmeli'
    return 'Yeterli'


def _stok_kpi_ozet(satirlar: list) -> dict:
    toplam_mevcut = 0.0
    for row in satirlar:
        row['durum'] = _stok_durum_hesapla(row)
        toplam_mevcut += float(row.get('mevcut') or 0)
    return {
        'toplam_kalem': len(satirlar),
        'toplam_mevcut': toplam_mevcut,
    }


@stok_durum_bp.route('/stok-durum')
@login_required
def stok_durum():
    """Stok Durum — şimdilik yalnızca arayüz (örnek veri). Backend sonra bağlanacak."""
    sd, ed = get_date_range()
    satirlar = [dict(r) for r in ORNEK_SATIRLAR]
    kpi = _stok_kpi_ozet(satirlar)
    return render_template(
        'stok_durum.html',
        start_date=sd,
        end_date=ed,
        page_sql_kodlari=PAGE_SQL_KODLARI,
        satirlar=satirlar,
        kpi=kpi,
    )
