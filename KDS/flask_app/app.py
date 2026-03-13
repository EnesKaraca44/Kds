from flask import Flask, session, redirect, url_for, request
from functools import wraps
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ayarlar import SECRET_KEY


def login_required(f):
    """Giriş kontrolü decorator'ü."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.config['SESSION_TYPE'] = 'filesystem'

    # Jinja2 Template'lerine yardımcı fonksiyonlar ekle
    @app.template_filter('turkish_number')
    def turkish_number_filter(value, decimals=2):
        """Sayıyı Türkçe formatta biçimlendirir."""
        try:
            value = float(value)
            if decimals == 0:
                formatted = f"{value:,.0f}"
            else:
                formatted = f"{value:,.{int(decimals)}f}"
            formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
            return formatted
        except (ValueError, TypeError):
            return str(value)

    # Tüm template'lere login bilgisini otomatik gönder
    @app.context_processor
    def inject_user():
        return dict(
            logged_in_user=session.get('logged_in_user', ''),
            nav_items={
                'ANA MODÜLLER': [
                    {'url': '/dashboard', 'icon': '🏠', 'label': 'Ana Sayfa'},
                    {'url': '/hekim-puan', 'icon': '🏵️', 'label': 'Hekim Hizmet Puan Analiz'},
                    {'url': '/poliklinik', 'icon': '👥', 'label': 'Hekim Poliklinik Hasta'},
                    {'url': '/tedavi', 'icon': '🩺', 'label': 'Tedavi Grupları Analizi'},
                    {'url': '/malzeme', 'icon': '📦', 'label': 'Kurum Malzeme Tüketim'},
                    {'url': '/yabanci-hasta', 'icon': '🌐', 'label': 'Yabancı Hasta Analizi', 'badge': 'YENİ'},
                    {'url': '/randevu', 'icon': '📅', 'label': 'Hekim Randevu Analizi'},
                    {'url': '/gelir', 'icon': '💰', 'label': 'Kurum Gelir Analiz'},
                    {'url': '/sterilizasyon', 'icon': '💉', 'label': 'Sterilizasyon Maliyet'},
                    {'url': '/sevk', 'icon': '📤', 'label': 'Hekim Sevk Sayıları'},
                ],
                'DİĞER': [
                    {'url': '/tibbi-atik', 'icon': '⚗️', 'label': 'Tıbbi Atık Analizi'},
                    {'url': '/protez', 'icon': '🦷', 'label': 'Protez Analizi'},
                    {'url': '/rontgen', 'icon': '🩻', 'label': 'Röntgen Analizi'},
                ]
            }
        )

    # Blueprint'leri kaydet
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.hekim_puan import hekim_puan_bp
    from routes.poliklinik import poliklinik_bp
    from routes.tedavi import tedavi_bp
    from routes.malzeme import malzeme_bp
    from routes.yabanci_hasta import yabanci_hasta_bp
    from routes.randevu import randevu_bp
    from routes.gelir import gelir_bp
    from routes.sterilizasyon import sterilizasyon_bp
    from routes.sevk import sevk_bp
    from routes.tibbi_atik import tibbi_atik_bp
    from routes.protez import protez_bp
    from routes.rontgen import rontgen_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(hekim_puan_bp)
    app.register_blueprint(poliklinik_bp)
    app.register_blueprint(tedavi_bp)
    app.register_blueprint(malzeme_bp)
    app.register_blueprint(yabanci_hasta_bp)
    app.register_blueprint(randevu_bp)
    app.register_blueprint(gelir_bp)
    app.register_blueprint(sterilizasyon_bp)
    app.register_blueprint(sevk_bp)
    app.register_blueprint(tibbi_atik_bp)
    app.register_blueprint(protez_bp)
    app.register_blueprint(rontgen_bp)

    # Kök URL yönlendirmesi
    @app.route('/')
    def index():
        if session.get('logged_in'):
            return redirect(url_for('dashboard.dashboard'))
        return redirect(url_for('auth.login'))

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
