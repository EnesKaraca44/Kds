# KDS Python Kütüphaneleri

Bu doküman, `flask_app` uygulamasının kullandığı Python paketlerini listeler.

---

## Kurulum

```powershell
cd flask_app
powershell -ExecutionPolicy Bypass -File .\kurulum.ps1
```

Detay: [SERVIS_KURULUMU.md](SERVIS_KURULUMU.md)

Güncel sürümleri görmek için:

```powershell
venv\Scripts\python.exe -m pip list
```

---

## Doğrudan bağımlılıklar (`requirements.txt`)

| Paket | Kullanım |
|-------|----------|
| **Flask** | Web uygulaması, routing, session, template |
| **Waitress** | Üretim WSGI sunucusu (`run_server.py`, Windows servisi) |
| **pyodbc** | MS SQL Server ODBC bağlantısı (`database/baglanti.py`) |
| **pandas** | SQL sonuçlarını DataFrame olarak işleme, gruplama, filtreleme |
| **plotly** | İnteraktif grafikler (Express / Graph Objects) |
| **pycryptodome** | Şifreleme ve hash (`crypto_system_functions.py`, giriş) |

---

## Kurulu paketler (venv — otomatik gelenler dahil)

Test ortamında (`Python 3.10`) yüklü sürümler:

| Paket | Sürüm | Rol |
|-------|-------|-----|
| Flask | 3.1.3 | Ana web framework |
| Werkzeug | 3.1.8 | Flask HTTP/WSGI altyapısı |
| Jinja2 | 3.1.6 | HTML şablon motoru |
| MarkupSafe | 3.0.3 | Jinja2 güvenli string |
| itsdangerous | 2.2.0 | Flask session imzalama |
| blinker | 1.9.0 | Flask sinyal desteği |
| click | 8.3.3 | Flask CLI |
| waitress | 3.0.2 | Üretim sunucusu |
| pandas | 2.3.3 | Veri analizi |
| numpy | 2.2.6 | pandas sayısal hesap (bağımlılık) |
| python-dateutil | 2.9.0.post0 | Tarih ayrıştırma (pandas) |
| pytz | 2026.2 | Saat dilimi (pandas) |
| tzdata | 2026.2 | IANA saat dilimi verisi |
| plotly | 6.7.0 | Grafikler |
| narwhals | 2.21.0 | plotly / pandas uyumluluk katmanı |
| packaging | 26.2 | Paket meta verisi |
| pyodbc | 5.3.0 | SQL Server ODBC |
| pycryptodome | 3.23.0 | AES, SHA-256 |
| colorama | 0.4.6 | Windows terminal renkleri (click) |
| six | 1.17.0 | python-dateutil bağımlılığı |

---

## Projede kullanılmayan / kurulu olmayan paketler

| Paket | Durum |
|-------|--------|
| **SQLAlchemy** | **Kullanılmıyor.** Veritabanı erişimi doğrudan `pyodbc` ile yapılır. pandas bazen “SQLAlchemy connectable kullanın” uyarısı verebilir; bu normaldir, zorunlu değildir. |
| **cryptography** | Kurulu değil; şifreleme için `pycryptodome` yeterli. |
| **django, fastapi** | Kullanılmıyor. |

---

## Sistem gereksinimleri (Python paketi değil)

| Bileşen | Açıklama |
|---------|----------|
| **Python 3.10+** | Sanal ortam |
| **ODBC Driver 17 for SQL Server** | `pyodbc` için Windows sürücüsü (`ayarlar.py` → `DB_DRIVER`) |
| **NSSM** | İsteğe bağlı Windows servisi (`tools/nssm/`) |
| **Rapor SQL API** | Harici HTTP servisi (varsayılan port `8053`) |

---

## Kodda kullanım özeti

```
Flask / Jinja2     → app.py, routes/*, templates/*
Waitress           → run_server.py
pandas             → database/*_sorgular.py, routes/*
plotly             → routes/* (grafik HTML üretimi)
pyodbc             → database/baglanti.py
pycryptodome       → crypto_system_functions.py, auth
urllib (stdlib)    → database/sql_api_client.py (Rapor API)
```

---

## Yeni paket ekleme

1. `pip install <paket>`
2. `requirements.txt` dosyasına paket adını ekleyin
3. Bu dokümandaki tabloları güncelleyin

```powershell
pip freeze > requirements-full.txt   # tüm sürümler (isteğe bağlı yedek)
```
