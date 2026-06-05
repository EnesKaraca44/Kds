from flask import Flask, session, redirect, url_for, request
from functools import wraps
import os
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ayarlar import SECRET_KEY
from database.auth_dao import get_user_menu_labels
from jinja_loader import ResilientFileSystemLoader


def _nav_compare_key(label: str) -> str:
    """KDS_LINK_TANIM ile kod icindeki etiketleri i/İ/ı ve birlesim farklarina toleransli karsilastir."""
    if not label:
        return ""
    t = unicodedata.normalize("NFKC", str(label).strip())
    t = t.replace("İ", "i").replace("I", "i").replace("ı", "i")
    return t.casefold()


def _menu_lookup(menu_dict: dict, canonical_label: str):
    """
    menu_dict'te canonical_label ile eslesen kayit.
    Donus: (url_code, db_key); eslesme yoksa (None, None).
    """
    if not menu_dict or not canonical_label:
        return None, None
    want = _nav_compare_key(canonical_label)
    for k, v in menu_dict.items():
        if _nav_compare_key(k) == want:
            return v, k
    return None, None


def _nav_insert_after(items_list: list, after_label: str, new_item: dict) -> None:
    """after_label ile ayni sayilan ogeyi bulup hemen altina new_item ekle; yoksa sona ekle."""
    want = _nav_compare_key(after_label)
    for idx, it in enumerate(items_list):
        if _nav_compare_key(it.get("label", "")) == want:
            items_list.insert(idx + 1, dict(new_item))
            return
    items_list.append(dict(new_item))


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
    # Windows servisinde ANSI kaydedilmis .html sablonlari icin (UnicodeDecodeError onlemi)
    app.jinja_loader = ResilientFileSystemLoader(os.path.join(app.root_path, app.template_folder))

    @app.after_request
    def _ensure_utf8_html_response(response):
        ctype = (response.content_type or "").lower()
        if ctype.startswith("text/") or ctype == "application/json":
            response.charset = "utf-8"
        return response

    default_nav_items = {
        'ANA MODÜLLER': [
            {'url': '/dashboard', 'icon': '🏠', 'label': 'Ana Sayfa'},
            {'url': '/personel-sorgulama', 'icon': '📋', 'label': 'Personel Sorgulama'},
            {'url': '/hekim-puan', 'icon': '🏵️', 'label': 'Hekim Hizmet Puan Analiz'},
            {'url': '/poliklinik', 'icon': '🏥', 'label': 'Hekim Poliklinik Hasta'},
            {'url': '/tedavi', 'icon': '🧪', 'label': 'Tedavi Grupları Analizi'},
            {'url': '/tedavi-kartlari', 'icon': '🧾', 'label': 'Tedavi Kartları Analizi'},
            {'url': '/malzeme', 'icon': '📦', 'label': 'Kurum Malzeme Tüketim'},
            {'url': '/yabanci-hasta', 'icon': '🌐', 'label': 'Yabancı Hasta Analizi'},
            {'url': '/randevu', 'icon': '📅', 'label': 'Hekim Randevu Analizi'},
            {'url': '/gelir', 'icon': '💰', 'label': 'Kurum Gelir Analiz'},
            {'url': '/cari-sorusturma', 'icon': '📒', 'label': 'Cari Soruşturma'},
            {'url': '/sterilizasyon', 'icon': '💉', 'label': 'Sterilizasyon Maliyet'},
            {'url': '/sevk', 'icon': '📤', 'label': 'Hekim Sevk Sayıları'},
        ],
        'DİĞER': [
            {'url': '/tibbi-atik', 'icon': '⚗️', 'label': 'Tıbbi Atık Analizi'},
            {'url': '/protez', 'icon': '🦷', 'label': 'Protez Analizi'},
            {'url': '/protez-takibi', 'icon': '🧾', 'label': 'Protez Takibi'},
            {'url': '/rontgen', 'icon': '🦷', 'label': 'Röntgen Analizi'},
        ]
    }

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
        nav_items = default_nav_items
        kullanici_id = session.get('user_id')

        if kullanici_id:
            menu_dict = get_user_menu_labels(kullanici_id)
            if menu_dict:
                filtered_nav = {}
                for group_name, items in default_nav_items.items():
                    matched_items = []
                    for item in items:
                        label = item.get('label')
                        db_path, db_key = _menu_lookup(menu_dict, label)
                        if db_key is not None:
                            if db_path:
                                item = dict(item)
                                if db_path.startswith('http'):
                                    item['url'] = db_path
                                else:
                                    path = db_path if db_path.startswith('/') else '/' + db_path
                                    item['url'] = path
                            matched_items.append(item)
                    if matched_items:
                        filtered_nav[group_name] = matched_items

                # Gecis donemi: "Tedavi Kartlari Analizi" menusu DB'de henuz tanimli degilse,
                # "Tedavi Gruplari Analizi" yetkisi olan kullanicilara yeni sayfayi da goster.
                _, tedavi_grup_db_key = _menu_lookup(menu_dict, "Tedavi Grupları Analizi")
                if tedavi_grup_db_key is not None:
                    tedavi_kartlari_item = None
                    for group_name, items in default_nav_items.items():
                        for item in items:
                            if item.get('label') == 'Tedavi Kartları Analizi':
                                tedavi_kartlari_item = (group_name, item)
                                break
                        if tedavi_kartlari_item:
                            break

                    if tedavi_kartlari_item:
                        target_group, target_item = tedavi_kartlari_item
                        filtered_nav.setdefault(target_group, [])
                        already_exists = any(
                            _nav_compare_key(i.get('label', '')) == _nav_compare_key('Tedavi Kartları Analizi')
                            for i in filtered_nav[target_group]
                        )
                        if not already_exists:
                            _nav_insert_after(
                                filtered_nav[target_group],
                                "Tedavi Grupları Analizi",
                                dict(target_item),
                            )

                # Gecis donemi: "Protez Takibi" menusu DB'de henuz tanimli degilse,
                # "Protez Analizi" yetkisi olan kullanicilara yeni sayfayi da goster.
                _, protez_db_key = _menu_lookup(menu_dict, "Protez Analizi")
                if protez_db_key is not None:
                    protez_takibi_item = None
                    for group_name, items in default_nav_items.items():
                        for item in items:
                            if item.get('label') == 'Protez Takibi':
                                protez_takibi_item = (group_name, item)
                                break
                        if protez_takibi_item:
                            break

                    if protez_takibi_item:
                        target_group, target_item = protez_takibi_item
                        filtered_nav.setdefault(target_group, [])
                        already_exists = any(
                            _nav_compare_key(i.get('label', '')) == _nav_compare_key('Protez Takibi')
                            for i in filtered_nav[target_group]
                        )
                        if not already_exists:
                            _nav_insert_after(
                                filtered_nav[target_group],
                                "Protez Analizi",
                                dict(target_item),
                            )

                if filtered_nav:
                    nav_items = filtered_nav

        return dict(
            logged_in_user=session.get('logged_in_user', ''),
            nav_items=nav_items
        )

    @app.context_processor
    def inject_page_sql_helpers():
        """Her sayfada base.html icin: page_sql_kodlari (route gecmediyse None) ve panel fonksiyonu."""

        def page_sql_api_satirlari(keys):
            from database.sql_api_client import page_sql_api_kodlari_satirlari

            if not keys:
                return []
            return page_sql_api_kodlari_satirlari(keys)

        return dict(page_sql_kodlari=None, page_sql_api_satirlari=page_sql_api_satirlari)

    # Blueprint'leri kaydet
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.hekim_puan import hekim_puan_bp
    from routes.poliklinik import poliklinik_bp
    from routes.tedavi import tedavi_bp
    from routes.tedavi_kartlari import tedavi_kartlari_bp
    from routes.malzeme import malzeme_bp
    from routes.yabanci_hasta import yabanci_hasta_bp
    from routes.randevu import randevu_bp
    from routes.gelir import gelir_bp
    from routes.sterilizasyon import sterilizasyon_bp
    from routes.sevk import sevk_bp
    from routes.tibbi_atik import tibbi_atik_bp
    from routes.protez import protez_bp
    from routes.protez_takibi import protez_takibi_bp
    from routes.rontgen import rontgen_bp
    from routes.personel_sorgulama import personel_sorgulama_bp
    from routes.cari_sorusturma import cari_sorusturma_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(hekim_puan_bp)
    app.register_blueprint(poliklinik_bp)
    app.register_blueprint(tedavi_bp)
    app.register_blueprint(tedavi_kartlari_bp)
    app.register_blueprint(malzeme_bp)
    app.register_blueprint(yabanci_hasta_bp)
    app.register_blueprint(randevu_bp)
    app.register_blueprint(gelir_bp)
    app.register_blueprint(sterilizasyon_bp)
    app.register_blueprint(sevk_bp)
    app.register_blueprint(tibbi_atik_bp)
    app.register_blueprint(protez_bp)
    app.register_blueprint(protez_takibi_bp)
    app.register_blueprint(rontgen_bp)
    app.register_blueprint(personel_sorgulama_bp)
    app.register_blueprint(cari_sorusturma_bp)

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
