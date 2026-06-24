from flask import Blueprint, jsonify, render_template, request
import sys
import os
from datetime import date
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required
from routes.dashboard import get_date_range
from database.stok_durum_sorgular import stok_durum_verisi_yukle, stok_durum_detay_yukle

stok_durum_bp = Blueprint('stok_durum', __name__)

PAGE_SQL_KODLARI = ["stok_durum.stok_durum_verisi_yukle"]


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


def _str_val(val) -> str:
    if isinstance(val, pd.Series):
        for item in val:
            s = _str_val(item)
            if s:
                return s
        return ''
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ''
    return str(val).strip()


def _format_son_kullanim(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ''
    if hasattr(val, 'strftime'):
        try:
            return val.strftime('%d.%m.%Y')
        except (ValueError, OSError):
            return ''
    s = _str_val(val)
    return s if s else ''


def _seri_lot(row: pd.Series) -> str:
    for col in ('shSeriLotNumber', 'shKunyeNo', 'shBatchNo'):
        if col in row.index:
            s = _str_val(row.get(col))
            if s:
                return s
    return ''


def _dataframe_to_satirlar(df: pd.DataFrame) -> list:
    if df is None or df.empty:
        return []

    if 'RowNumber' in df.columns:
        df = df.sort_values('RowNumber', kind='stable')
    elif 'shStokAd' in df.columns:
        df = df.sort_values('shStokAd', kind='stable')

    satirlar = []
    for _, row in df.iterrows():
        mevcut = float(row.get('shMevcutMiktar') or 0)
        maximum = float(row.get('maxStokMiktar') or 0)
        stok_fazlasi = max(0.0, mevcut - maximum) if maximum > 0 else 0.0

        satirlar.append({
            'stok_kart_id': _str_val(row.get('shStokKartId')),
            'hareket_turu': _str_val(row.get('hareketTurBelgeAd')) or '—',
            'malzeme_kodu': _str_val(row.get('shStokKod')),
            'malzeme_adi': _str_val(row.get('shStokAd')),
            'malzeme_aciklama': _str_val(row.get('shStokAciklama')) or _str_val(row.get('shStokAd')),
            'birim': _str_val(row.get('shOlcuBirimAd')),
            'giris': float(row.get('shMiktar') or 0),
            'cikis': float(row.get('shCikisMiktar') or 0),
            'mevcut': mevcut,
            'minimum': float(row.get('minStokMiktar') or 0),
            'kritik': float(row.get('kritikStokMiktar') or 0),
            'maximum': maximum,
            'yillik': float(row.get('yillikStokMiktar') or 0),
            'stok_fazlasi': stok_fazlasi,
            'son_kullanim': _format_son_kullanim(row.get('shVadeTarih')),
            'seri_lot': _seri_lot(row),
        })
    return satirlar


def _son_bir_yil_araligi():
    ed = date.today()
    try:
        sd = ed.replace(year=ed.year - 1)
    except ValueError:
        sd = ed.replace(year=ed.year - 1, day=28)
    return sd.isoformat(), ed.isoformat()


@stok_durum_bp.route('/stok-durum/detay')
@login_required
def stok_durum_detay_api():
    stok_id = (request.args.get('stok_id') or request.args.get('stok_kart_id') or '').strip()
    if not stok_id:
        return jsonify({'ozet': {}, 'satirlar': [], 'count': 0, 'error': 'stok_id gerekli'}), 400

    start_str, end_str = _son_bir_yil_araligi()
    data = stok_durum_detay_yukle(stok_id, start_str, end_str)
    data['start_date'] = start_str
    data['end_date'] = end_str
    return jsonify(data)


@stok_durum_bp.route('/stok-durum')
@login_required
def stok_durum():
    sd, ed = get_date_range()
    df = stok_durum_verisi_yukle(sd.isoformat(), ed.isoformat())
    satirlar = _dataframe_to_satirlar(df)
    kpi = _stok_kpi_ozet(satirlar)

    return render_template(
        'stok_durum.html',
        start_date=sd,
        end_date=ed,
        page_sql_kodlari=PAGE_SQL_KODLARI,
        satirlar=satirlar,
        kpi=kpi,
        no_data=not satirlar,
    )
