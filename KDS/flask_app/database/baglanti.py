import pyodbc
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ayarlar import DATABASE


def baglanti_olustur():
    """Veritabanına bağlantı oluşturur."""
    try:
        conn = pyodbc.connect(
            f"DRIVER={DATABASE['driver']};"
            f"SERVER={DATABASE['server']};"
            f"DATABASE={DATABASE['database']};"
            f"UID={DATABASE['username']};"
            f"PWD={DATABASE['password']}"
        )
        return conn
    except Exception as e:
        print(f"❌ Veritabanı bağlantı hatası: {e}")
        return None
