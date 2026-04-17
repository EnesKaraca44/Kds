from flask import Blueprint, render_template, request, session
from datetime import date, timedelta
import datetime
import time
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required
from database.dinamik_gelir_sorgular import dinamik_dashboard_metrikleri_getir
from database.baglanti import baglanti_olustur

dashboard_bp = Blueprint('dashboard', __name__)


def get_date_range():
    """URL parametrelerinden veya varsayılandan tarih aralığını alır."""
    today = date.today()
    quick = request.args.get('quick')

    if not quick:
        # Keep user's last selected date range across page switches/tabs.
        sd_session = session.get('start_date')
        ed_session = session.get('end_date')
        if sd_session and ed_session:
            try:
                sd = date.fromisoformat(sd_session)
                ed = date.fromisoformat(ed_session)
                session['start_date'] = sd.isoformat()
                session['end_date'] = ed.isoformat()
                return sd, ed
            except ValueError:
                pass
        quick = 'bu-ay'
    
    if quick == 'bugun':
        sd, ed = today, today
    elif quick == 'dun':
        sd, ed = today - timedelta(days=1), today - timedelta(days=1)
    elif quick == 'son-7':
        sd, ed = today - timedelta(days=7), today
    elif quick == 'son-30':
        sd, ed = today - timedelta(days=30), today
    elif quick == 'bu-ay':
        sd, ed = today.replace(day=1), today
    elif quick == 'gecen-ay':
        first_current = today.replace(day=1)
        ed = first_current - timedelta(days=1)
        sd = ed.replace(day=1)
    elif quick == 'bu-yil':
        sd, ed = date(today.year, 1, 1), today
    elif quick == 'gecen-yil':
        last_year = today.year - 1
        sd = date(last_year, 1, 1)
        ed = date(last_year, 12, 31)
    elif quick == 'ozel':
        sd_str = request.args.get('start')
        ed_str = request.args.get('end')
        try:
            # If empty string or invalid format, fallback to default month start/today
            sd = date.fromisoformat(sd_str) if sd_str else today.replace(day=1)
            ed = date.fromisoformat(ed_str) if ed_str else today
        except (ValueError, TypeError):
            sd, ed = today.replace(day=1), today
    else:
        sd, ed = today.replace(day=1), today

    session['start_date'] = sd.isoformat()
    session['end_date'] = ed.isoformat()
    return sd, ed


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    sd, ed = get_date_range()
    
    current_hour = datetime.datetime.now().hour
    greeting = "İyi Günler" if 9 <= current_hour < 18 else "İyi Çalışmalar"
    
    # Finansal performans verileri
    metrics = {}
    query_time = 0
    db_status = 'error'
    
    start_perf = time.time()
    try:
        df_latest = dinamik_dashboard_metrikleri_getir(sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d'))
        query_time = round(time.time() - start_perf, 3)
        
        if not df_latest.empty:
            m = df_latest.iloc[0]
            avg_val = m['ToplamTutar'] / m['ToplamHasta'] if m['ToplamHasta'] > 0 else 0
            metrics = {
                'toplam_hasta': int(m['ToplamHasta']),
                'toplam_tutar': m['ToplamTutar'],
                'avg_val': avg_val,
                'fatura_no': m['FATURA_NO'],
            }
    except Exception as e:
        metrics['error'] = str(e)
    
    # DB bağlantı kontrolü
    try:
        conn = baglanti_olustur()
        if conn:
            db_status = 'ok'
            conn.close()
    except:
        db_status = 'error'
    
    return render_template('dashboard.html',
        greeting=greeting,
        start_date=sd,
        end_date=ed,
        metrics=metrics,
        query_time=query_time,
        db_status=db_status,
        current_time=datetime.datetime.now().strftime("%H:%M:%S"),
        quick_choice=request.args.get('quick', 'bu-ay'),
    )
