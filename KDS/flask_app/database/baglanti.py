import pyodbc
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ayarlar import DATABASE
from crypto_system_functions import decrypt_string_v2, encrypt_string_v2


_BASE64_RE = re.compile(r"^[A-Za-z0-9+/]+={0,2}$")


def _normalize_server(server: str) -> str:
    """SQL Server adresini ODBC ile uyumlu hale getirir."""
    if not isinstance(server, str):
        return ""

    server = server.strip()
    if not server:
        return ""

    # "host:port" -> "host,port"
    if ":" in server and "," not in server:
        host, port = server.rsplit(":", 1)
        if port.isdigit():
            server = f"{host},{port}"

    # Named Pipes fallback'ini engellemek icin TCP zorla.
    if not server.lower().startswith("tcp:"):
        server = f"tcp:{server}"

    return server


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

        server = _normalize_server(DATABASE.get("server", ""))

        conn_str = (
            f"DRIVER={DATABASE['driver']};"
            f"SERVER={server};"
            f"DATABASE={DATABASE['database']};"
            f"UID={DATABASE['username']};"
            f"PWD={password};"
            f"Connection Timeout={int(os.environ.get('KDS_DB_CONN_TIMEOUT', '5'))};"
            f"Login Timeout={int(os.environ.get('KDS_DB_LOGIN_TIMEOUT', '5'))};"
            "TrustServerCertificate=yes;"
        )
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        # Windows konsol encoding'lerinde emoji bazen hata çıkarabiliyor.
        print(f"Veritabani baglanti hatasi: {e}")
        return None
