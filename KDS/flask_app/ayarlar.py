import os

# Flask ayarları
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "kds-super-secret-key-2026")

# Veritabanı ayarları (eski secrets.toml'dan taşındı)
DATABASE = {
    "server": "193.255.140.195:50602",
    "database": "DEAL",
    "username": "sa",
    "password": "enc:Z/4EPURZYeiloayNccO7ECHsixCKeQynNBknaFGrvYM=",
    "driver": "{ODBC Driver 17 for SQL Server}",
}

# Menü kişiselleştirme tablosunun bulunduğu ikinci veritabanı
DATABASE_MENU = {
    "server": os.environ.get("MENU_DB_SERVER", "192.168.12.17"),
    "database": os.environ.get("MENU_DB_NAME", "DEAL_CAPA_YENI"),
    "username": os.environ.get("MENU_DB_USERNAME", "sa"),
    "password": os.environ.get("MENU_DB_PASSWORD", "meta26.soft"),
    "driver": os.environ.get("MENU_DB_DRIVER", DATABASE["driver"]),
}

# Kullanıcı bilgileri
CREDENTIALS = {
    "admin": "12345",
    "user": "",
}



