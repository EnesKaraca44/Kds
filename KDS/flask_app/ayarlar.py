import os

# Flask ayarları
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "kds-super-secret-key-2026")

# Veritabanı ayarları (eski secrets.toml'dan taşındı)
DATABASE = {
    "server": "192.168.12.17",
    "database": "MAMAKADSM_HASTAM",
    "username": "metasoft",
    "password": "Meta26.soft",
    "driver": "{ODBC Driver 17 for SQL Server}",
}

# Kullanıcı bilgileri
CREDENTIALS = {
    "admin": "12345",
    "user": "",
}
