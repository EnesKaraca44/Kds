import sys
import os

# flask_app klasörünü Python yoluna ekliyoruz ki modülleri bulabilsin
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'flask_app')))

try:
    from database.sql_api_client import _get_remote_sql_single_code
    
    kod_adi = "HEKIM_PUAN_TAB1"
    print(f"API'ye bağlanılıyor ve '{kod_adi}' kodu sorgulanıyor...\n")
    
    sonuc = _get_remote_sql_single_code(kod_adi)
    
    print("-" * 50)
    if sonuc is None:
        print("SONUÇ: BAŞARISIZ (BOŞ)")
        print(f"HATA: API '{kod_adi}' kodunu bulamadı veya API çalışmıyor.")
    else:
        print("SONUÇ: BAŞARILI (DOLU)")
        print(f"API'den Gelen SQL Uzunluğu: {len(sonuc)} karakter")
        print("Gelen SQL:")
        print(sonuc)
    print("-" * 50)
    
except Exception as e:
    print(f"Beklenmedik bir hata oluştu: {e}")

input("\nÇıkmak için Enter'a basın...")
