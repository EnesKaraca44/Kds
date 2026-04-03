import pyodbc
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ayarlar import DATABASE, DATABASE_MENU
from crypto_system_functions import decrypt_string_v2, encrypt_string_v2


_BASE64_RE = re.compile(r"^[A-Za-z0-9+/]+={0,2}$")


def _maybe_decrypt_password(password: str) -> str:
    """
    Ayarlar dosyasında şifre düz veya şifreli saklanabiliyor.
    - "enc:<base64>" ise decrypt edilir.
    - Değilse: değer bizim deterministic AES+Base64 çıktımız gibi görünüyorsa decrypt edilir.
      (Doğrulama: decrypt -> encrypt roundtrip aynı string'i üretmeli)
    """
    if not isinstance(password, str) or password == "":
        return ""

    if password.startswith("enc:"):
        return decrypt_string_v2(password[4:]) or ""

    # "enc:" kullanılmadan şifreli değer yazıldıysa otomatik algıla.
    # Heuristik + roundtrip doğrulama: decrypt ettikten sonra tekrar encrypt edince aynı olmalı.
    if (
        len(password) >= 24
        and (len(password) % 4) == 0
        and _BASE64_RE.match(password) is not None
    ):
        try:
            plain = decrypt_string_v2(password)
            if plain and encrypt_string_v2(plain) == password:
                return plain
        except Exception:
            pass

    return password


def baglanti_olustur():
    """Veritabanına bağlantı oluşturur."""
    try:
        password = _maybe_decrypt_password(DATABASE.get("password", ""))

        server = DATABASE.get("server", "")
        # SQL Server ODBC için port ayırıcısı genelde virgüldür: "host,port"
        # Ayarlarda "host:port" gelirse otomatik dönüştürelim.
        if isinstance(server, str) and ":" in server and "," not in server:
            host, port = server.rsplit(":", 1)
            if port.isdigit():
                server = f"{host},{port}"

        conn_str = (
            f"DRIVER={DATABASE['driver']};"
            f"SERVER={server};"
            f"DATABASE={DATABASE['database']};"
            f"UID={DATABASE['username']};"
            f"PWD={password};"
        )
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        # Windows konsol encoding'lerinde emoji bazen hata çıkarabiliyor.
        print(f"Veritabani baglanti hatasi: {e}")
        return None


def baglanti_olustur_menu_db():
    """Menü kişiselleştirme veritabanına bağlantı oluşturur."""
    try:
        password = _maybe_decrypt_password(DATABASE_MENU.get("password", ""))

        server = DATABASE_MENU.get("server", "")
        if isinstance(server, str) and ":" in server and "," not in server:
            host, port = server.rsplit(":", 1)
            if port.isdigit():
                server = f"{host},{port}"

        conn_str = (
            f"DRIVER={DATABASE_MENU['driver']};"
            f"SERVER={server};"
            f"DATABASE={DATABASE_MENU['database']};"
            f"UID={DATABASE_MENU['username']};"
            f"PWD={password};"
        )
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        print(f"Menu DB baglanti hatasi: {e}")
        return None
