# Karar Destek Sistemi (KDS)

Hastaneler ve sağlık kuruluşları için geliştirilmiş, kapsamlı veri analizi ve raporlama sunan web tabanlı bir Karar Destek Sistemi.

## 🚀 Proje Hakkında

Bu uygulama, sağlık yöneticilerinin ve hekimlerin operasyonel verileri anlamlandırmasına, performans takibi yapmasına ve stratejik kararlar almasına yardımcı olmak amacıyla tasarlanmıştır. Flask tabanlı modern bir mimari üzerine inşa edilmiştir ve hastane bilgi yönetim sistemleri (HBYS) ile entegre çalışacak şekilde yapılandırılmıştır.

## 🛠️ Temel Modüller

Uygulama aşağıdaki ana analiz ve raporlama modüllerini içermektedir:

- **🏠 Ana Sayfa (Dashboard):** Kurumun genel durumunu gösteren özet grafikler ve göstergeler.
- **👤 Personel Sorgulama:** Personel bazlı detaylı veri ve performans analizi.
- **🏵️ Hekim Hizmet Puan Analizi:** Hekimlerin sunduğu hizmetlerin puan bazlı takibi.
- **👥 Poliklinik & Hasta Analizi:** Poliklinik yoğunluğu ve hasta trafiği raporları.
- **🩺 Tedavi Grupları Analizi:** Yapılan tedavilerin gruplandırılmış maliyet ve sayı analizi.
- **📦 Kurum Malzeme Tüketim:** Stok ve malzeme kullanım verimliliği takibi.
- **🌐 Yabancı Hasta Analizi:** Uluslararası hasta trafiği ve gelir raporlaması.
- **📅 Randevu & Sadakat Analizi:** Randevu doluluk oranları ve hasta devamlılık verileri.
- **💰 Kurum Gelir Analizi:** Finansal durum ve gelir kaynaklarının detaylı dökümü.
- **💉 Sterilizasyon Maliyet Analizi:** Sterilizasyon birimi operasyonel maliyet takibi.
- **📤 Hekim Sevk Sayıları:** Kurum içi ve dışı sevk trafiği.
- **⚗️ Tıbbi Atık Analizi:** Atık yönetimi ve çevresel veri takibi.
- **🦷 Protez Takibi & Analizi:** Diş protez süreçlerinin uçtan uca yönetimi ve analizi.
- **🩻 Röntgen Analizi:** Görüntüleme birimi işlem hacmi ve raporlaması.

## 💻 Teknoloji Yığını

- **Backend:** Python / Flask
- **Veritabanı Erişimi:** pyodbc (MS SQL Server entegrasyonu)
- **Frontend:** HTML5, CSS3, JavaScript
- **Veri İşleme:** Pandas
- **Görselleştirme:** Plotly / Chart.js
- **Güvenlik:** AES-256 (Şifreli veri saklama), SHA-256 (Şifreleme)

## ⚙️ Kurulum

Projeyi yerel ortamınızda çalıştırmak için aşağıdaki adımları izleyebilirsiniz:

1.  **Depoyu Klonlayın:**
    ```bash
    git clone https://github.com/EnesKaraca44/Kds.git
    cd Kds
    ```

2.  **Sanal Ortam Oluşturun ve Aktifleştirin:**
    ```bash
    python -m venv venv
    # Windows için:
    venv\Scripts\activate
    # macOS/Linux için:
    source venv/bin/activate
    ```

3.  **Bağımlılıkları Yükleyin:**
    ```bash
    pip install flask pyodbc pandas plotly pycryptodome
    ```

4.  **Veritabanı Ayarları:**
    `KDS/flask_app/ayarlar.py` dosyasındaki veritabanı bağlantı bilgilerini kendi sisteminize göre güncelleyin.

5.  **Uygulamayı Başlatın:**
    ```bash
    python KDS/flask_app/app.py
    ```

## 📂 Proje Yapısı

```text
KDS/
├── flask_app/
│   ├── database/       # SQL sorguları ve veri erişim katmanı (DAO)
│   ├── routes/         # Flask Blueprint'leri ve sayfa yönlendirmeleri
│   ├── static/         # CSS, JavaScript ve Görsel varlıklar
│   ├── templates/      # Jinja2 HTML şablonları
│   ├── app.py          # Uygulama giriş noktası ve konfigürasyon
│   ├── ayarlar.py      # Veritabanı ve uygulama ayarları
│   └── utils.py        # Yardımcı fonksiyonlar
└── tools/              # Yardımcı araçlar ve ek modüller
```

## 🤝 Katkıda Bulunma

1. Bu depoyu çatallayın (Fork).
2. Yeni bir özellik dalı (Branch) oluşturun (`git checkout -b feature/yeniozellik`).
3. Değişikliklerinizi kaydedin (Commit) (`git commit -m 'Yeni özellik eklendi'`).
4. Dalınıza gönderin (Push) (`git push origin feature/yeniozellik`).
5. Bir Çekme İsteği (Pull Request) oluşturun.

---
**Enes Karaca** tarafından geliştirilmiştir.
