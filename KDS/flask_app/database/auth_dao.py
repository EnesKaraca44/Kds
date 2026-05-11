import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.baglanti import baglanti_olustur, baglanti_olustur_menu_db
from crypto_system_functions import encrypt_string_v2, string_to_sha256
from .cache_helper import ttl_cache

def find_username_from_tc(tc: str) -> str:
    """TC Kimlik no ile kullanıcı adını bulur."""
    if not tc or not tc.strip():
        print("UYARI: find_username_from_tc metoduna BOŞ TC geldi!")
        return ""
        
    kullanici_adi = ""
    conn = None
    try:
        conn = baglanti_olustur()
        if not conn:
            return ""
            
        cursor = conn.cursor()
        
        try:
            tc_param = int(tc.strip())
        except ValueError:
            print(f"HATA: TC Kimlik No sayısal değil! Gelen değer: {tc}")
            return ""
            
        sql = """
        SELECT TOP 1 k.KULLANICI_AD
        FROM KULLANICI as k WITH(NOLOCK)
        INNER JOIN KIMLIK as km WITH(NOLOCK) ON km.KIMLIK_ID = k.KIMLIK_ID
        WHERE 1=1
            AND (ISNULL(k.PSF_ID, 0) = 0)
            AND km.KIMLIK_TC_NO = ?
        """
        cursor.execute(sql, (tc_param,))
        row = cursor.fetchone()
        
        if row and row[0]:
            kullanici_adi = str(row[0])
            
    except Exception as e:
        print(f"HATA: Kullanıcı adı bulunurken veritabanı hatası oluştu: {e}")
    finally:
        if conn:
            conn.close()
            
    return kullanici_adi

def find_user_with_username_and_password(username: str, password_hash: str) -> dict | None:
    """Kullanıcı adı ve şifreye göre kullanıcı bilgilerini döndürür."""
    if not username or not password_hash:
        return None
        
    conn = None
    kullanici = None
    try:
        conn = baglanti_olustur()
        if not conn:
            return None
            
        cursor = conn.cursor()
        
        sql = """
        SELECT TOP 1 
            km.KIMLIK_ID as kimlikId, 
            k.KULLANICI_ID as kullaniciId, 
            k.KULLANICI_AD as kullaniciAd, 
            k.KULLANICI_SIFRE as kullaniciSifre, 
            (km.KIMLIK_AD + ' ' + km.KIMLIK_SOYAD) as kullaniciAdSoyad, 
            k.KULLANICI_EMAIL as kullaniciEmail, 
            k.KULLANICI_CEP_TELEFONU as kullaniciCepTelefonu, 
            k.KULLANICI_OLUSTURMA_TRH as kullaniciOlusturmaTrh, 
            k.MERKEZI_VERI_ID as merkeziVeriId, 
            k.KULLANICI_BLOKE_DURUM as kullaniciEngelDurum, 
            k.KULLANICI_BLOKE_TRH as kullaniciEngelTrh 
        FROM KULLANICI as k WITH(NOLOCK) 
        INNER JOIN KIMLIK as km WITH(NOLOCK) ON km.KIMLIK_ID = k.KIMLIK_ID 
        WHERE 1=1 
            AND (ISNULL(k.PSF_ID,0)=0) 
            AND k.KULLANICI_SIFRE = ? 
            AND ( 
                LTRIM(RTRIM(k.KULLANICI_AD)) = ? 
                OR LTRIM(RTRIM(k.KULLANICI_KIMLIK_TC)) = ? 
                OR (TRY_CAST(? AS BIGINT) IS NOT NULL AND km.KIMLIK_TC_NO = TRY_CAST(? AS BIGINT)) 
            )
        """
        
        username_clean = username.strip()
        # SQL Parametreleri (?, ?, ?, ?, ?)
        cursor.execute(sql, (password_hash, username_clean, username_clean, username_clean, username_clean))
        row = cursor.fetchone()
        
        if row:
            print(f"DEBUG: Kimlik bulundu! Ad: {row.kullaniciAdSoyad}")
            kullanici = {
                'kimlikId': row.kimlikId,
                'kullaniciId': row.kullaniciId,
                'kullaniciAd': row.kullaniciAd,
                'kullaniciAdSoyad': row.kullaniciAdSoyad,
                'kullaniciEmail': row.kullaniciEmail,
                'kullaniciCepTelefonu': row.kullaniciCepTelefonu,
                'merkeziVeriId': row.merkeziVeriId,
                'kullaniciEngelDurum': row.kullaniciEngelDurum,
            }
        else:
            print(f"DEBUG: Veritabanında eşleşen kullanıcı BULUNAMADI! username: '{username_clean}', denenen hash: '{password_hash}'")
            
    except Exception as e:
        print(f"HATA: find_user_with_username_and_password hatası: {e}")
    finally:
        if conn:
            conn.close()
            
    return kullanici


def authenticate(username: str, password_raw: str) -> dict | None:
    """Sisteme giriş işlemini yönetir (Java'daki logic ile birebir)."""
    try:
        print(f"DEBUG: authenticate() tetiklendi. username='{username}'")
        if not username or not password_raw:
            print("DEBUG: Kullanıcı adı veya şifre boş.")
            return None
            
        # password = SystemFunctions.StringToSha256(SystemFunctions.encryptString_V2(password))
        encrypted_v2 = encrypt_string_v2(password_raw)
        print(f"DEBUG: V2 Şifreleme çıktısı: '{encrypted_v2}'")
        if encrypted_v2 is None:
            return None
            
        password_hash = string_to_sha256(encrypted_v2)
        if not password_hash:
            return None
            
        username_clean = username.strip()
            
        # if(username.length() == 11 && isNumeric(username)){
        #    username = userDao.findUserNamefromTC(username);
        # }
        if len(username_clean) == 11 and username_clean.isdigit():
            user_from_tc = find_username_from_tc(username_clean)
            if user_from_tc:
                username_clean = user_from_tc
                
        # kullanici = userDao.findUserWithUsernameAndPassword(username, password);
        kullanici = find_user_with_username_and_password(username_clean, password_hash)
        
        return kullanici
    except Exception as e:
        print(f"HATA: authenticate metodunda beklenmedik hata: {e}")
        return None


def get_user_menu_links(kullanici_id: int, kimlik_id: int) -> set[int]:
    """Menu DB'den kullanıcıya ait KDS_LINK_ID listesini getirir."""
    if not kullanici_id or not kimlik_id:
        return set()

    conn = None
    try:
        conn = baglanti_olustur_menu_db()
        if not conn:
            return set()

        cursor = conn.cursor()
        sql = """
        SELECT kds.KDS_LINK_ID
        FROM KULLANICI_KDS as kds WITH(NOLOCK)
        WHERE kds.KULLANICI_ID = ?
          AND kds.KIMLIK_ID = ?
        """
        cursor.execute(sql, (kullanici_id, kimlik_id))
        rows = cursor.fetchall()

        menu_link_ids = set()
        for row in rows:
            try:
                menu_link_ids.add(int(row.KDS_LINK_ID))
            except Exception:
                continue
        return menu_link_ids
    except Exception as e:
        print(f"HATA: get_user_menu_links hatasi: {e}")
        return set()
    finally:
        if conn:
            conn.close()


@ttl_cache(maxsize=100, ttl=3600)
def get_user_menu_labels(kullanici_id: int) -> dict[str, str | None]:
    """
    KULLANICI_KDS + KULLANICI_KDS_LINK join ile
    kullanıcıya ait menü adı ve URL kodunu getirir.
    Dönüş: {"Ana Sayfa": "1.1", "Hekim Hizmet Puan Analiz": None, ...}
    """
    if not kullanici_id:
        return {}

    conn = None
    try:
        conn = baglanti_olustur_menu_db()
        if not conn:
            return {}

        cursor = conn.cursor()
        sql = """
        SELECT
            link.KDS_LINK_TANIM,
            COALESCE(NULLIF(kds.KDS_LINK_URL, ''), link.KDS_LINK_TANIM_URL) as EFFECTIVE_URL_CODE
        FROM KULLANICI_KDS as kds WITH(NOLOCK)
        INNER JOIN KULLANICI_KDS_LINK as link WITH(NOLOCK)
            ON link.KDS_LINK_ID = kds.KDS_LINK_ID
        WHERE kds.KULLANICI_ID = ?
        """
        cursor.execute(sql, (kullanici_id,))
        rows = cursor.fetchall()

        menu_dict = {}
        for row in rows:
            label = str(row.KDS_LINK_TANIM).strip() if row.KDS_LINK_TANIM is not None else ""
            url_code = str(row.EFFECTIVE_URL_CODE).strip() if row.EFFECTIVE_URL_CODE is not None else None
            if url_code == "":
                url_code = None
            if label:
                menu_dict[label] = url_code
        return menu_dict
    except Exception as e:
        print(f"HATA: get_user_menu_labels hatasi: {e}")
        return {}
    finally:
        if conn:
            conn.close()
