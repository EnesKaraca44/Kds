from flask import Blueprint, render_template
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required
from routes.dashboard import get_date_range

sterilizasyon_bp = Blueprint('sterilizasyon', __name__)

PAGE_SQL_KODLARI = [
    "local:Bu sayfada henüz rapor API çağrısı yok (örnek arayüz; canlı SQL bağlantısı route’ta tanımlı değil).",
]


@sterilizasyon_bp.route('/sterilizasyon')
@login_required
def sterilizasyon():
    """Sterilizasyon Maliyet — şimdilik yalnızca arayüz (örnek veri). Backend sonra bağlanacak."""
    sd, ed = get_date_range()
    return render_template('sterilizasyon.html', start_date=sd, end_date=ed, page_sql_kodlari=PAGE_SQL_KODLARI)
