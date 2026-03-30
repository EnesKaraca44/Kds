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

# Kullanıcı bilgileri
CREDENTIALS = {
    "admin": "12345",
    "user": "",
}



