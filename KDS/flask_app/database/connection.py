import pyodbc
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE


def get_db_connection():
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
