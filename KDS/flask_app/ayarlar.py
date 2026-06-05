import os

# Flask ayarları
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "kds-super-secret-key-2026")

# Veritabanı ayarları (eski secrets.toml'dan taşındı)
DATABASE = {
    "server": "193.255.97.111:62168",
    "database": "DEAL",
    "username": "metasoft",
    "password": "enc:vfhGRTK4IL5upsDBygM7PLZQJLKpH3eGAoWRArCpFbQ=",
    "driver": "{ODBC Driver 17 for SQL Server}",
}

# Menü linkleri için temel URL (domain kısmı)
MENU_BASE_URL = os.environ.get("MENU_BASE_URL", "http://127.0.0.1:5000")

# Kullanıcı bilgileri
CREDENTIALS = {
    "admin": "12345",
    "user": "",
}



