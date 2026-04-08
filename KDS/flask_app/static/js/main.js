/* ============================================
   KDS - Main JavaScript
   ============================================ */

// 1. Translations Dictionary
const translations = {
    'tr': {
        'Kurum Performans Yönetim Sistemi': 'Kurum Performans<br>Yönetim Sistemi',
        'Dashboard': 'Dashboard',
        'ANA MODÜLLER': 'ANA MODÜLLER',
        'Ana Sayfa': 'Ana Sayfa',
        'Hekim Hizmet Puan Analiz': 'Hekim Hizmet Puan Analiz',
        'Hekim Poliklinik Hasta': 'Hekim Poliklinik Hasta',
        'Tedavi Grupları Analizi': 'Tedavi Grupları Analizi',
        'Kurum Malzeme Tüketim': 'Kurum Malzeme Tüketim',
        'Yabancı Hasta Analizi': 'Yabancı Hasta Analizi',
        'Hekim Randevu Analizi': 'Hekim Randevu Analizi',
        'Kurum Gelir Analiz': 'Kurum Gelir Analiz',
        'Sterilizasyon Maliyet': 'Sterilizasyon Maliyet',
        'Ameliyat Kar-Zarar': 'Ameliyat Kar-Zarar',
        'Röntgen Analizleri': 'Röntgen Analizleri',
        'Fatura Analiz': 'Fatura Analiz',
        'Vezne Gelir Analiz': 'Vezne Gelir Analiz',
        'Ayaktan/Yatan Doluluk': 'Ayaktan/Yatan Doluluk',
        'Hekim Sevk Sayıları': 'Hekim Sevk Sayıları',
        'YARDIMCI MODÜLLER': 'YARDIMCI MODÜLLER',
        'DİĞER': 'DİĞER',
        'Tıbbi Atık Analizi': 'Tıbbi Atık Analizi',
        'Protez Analizi': 'Protez Analizi',
        'Röntgen Analizi': 'Röntgen Analizi',
        'Koyu': 'Koyu',
        'Açık': 'Açık',
        'Filtrele': '🔄 Filtrele',
        'Çıkış': '🚪 Çıkış',
        'Yükleniyor, lütfen bekleyin...': 'Yükleniyor, lütfen bekleyin...',
        'Günaydın': 'Günaydın',
        'İyi Günler': 'İyi Günler',
        'İyi Akşamlar': 'İyi Akşamlar',
        'Analiz periyodu': 'Analiz periyodu',
        '🚀 Finansal Performans Özeti': '🚀 Finansal Performans Özeti',
        'Toplam Hasta': 'Toplam Hasta',
        'Kişi': 'Kişi',
        'Güncel Kayıt': 'Güncel Kayıt',
        'Tahmini Toplam Gelir': 'Tahmini Toplam Gelir',
        'Tahakkuk Eden': 'Tahakkuk Eden',
        'Hasta Başına Düşen Ortalama Gelir': 'Hasta Başına Düşen Ortalama Gelir',
        'Verimlilik': 'Verimlilik',
        'Sistem Notu': 'Sistem Notu',
        'Veriler, seçili tarih aralığındaki güncel (canlı) hareketlerden konsolide edilmiştir.': 'Veriler, seçili tarih aralığındaki güncel (canlı) hareketlerden konsolide edilmiştir.',
        '🛠️ Sistem Sağlık Durumu': '🛠️ Sistem Sağlık Durumu',
        'Sunucu Bağlantısı': 'Sunucu Bağlantısı',
        '✅ Doğrulandı': '✅ Doğrulandı',
        '❌ Bağlantı Yok': '❌ Bağlantı Yok',
        'Sorgu Performance': 'Sorgu Performansı',
        'sn': 'sn',
        'Ölçülmedi': 'Ölçülmedi',
        'Son Güncelleme': 'Son Güncelleme',
        'Bugün': 'Bugün',
        'Dün': 'Dün',
        'Son 7 Gün': 'Son 7 Gün',
        'Son 30 Gün': 'Son 30 Gün',
        'Bu Ay': 'Bu Ay',
        'Geçen Ay': 'Geçen Ay',
        'Bu Yıl': 'Bu Yıl',
        'Geçen Yıl': 'Geçen Yıl',
        'Özel': 'Özel',
        'Aktif Dönem': 'Aktif Dönem',
        'Hekim Poliklinik Hasta Analizi': 'Hekim Poliklinik Hasta Analizi',
        'Toplam Kayıt': 'Toplam Kayıt',
        'Benzersiz Hasta': 'Benzersiz Hasta',
        'Aktif Hekim': 'Aktif Hekim',
        'Branş Sayısı': 'Branş Sayısı',
        '📊 Performans (Sıralama Kriterli)': '📊 Performans (Sıralama Kriterli)',
        '📈 Kurum & Trend': '📈 Kurum & Trend',
        '🔥 Yoğunluk Analizi': '🔥 Yoğunluk Analizi',
        '🔍 Hekim Detay': '🔍 Hekim Detay',
        'SIRALAMA KRİTERİ:': 'SIRALAMA KRİTERİ:',
        '📋 Kayıt Sayısı': '📋 Kayıt Sayısı',
        '👥 Benzersiz Hasta Sayısı': '👥 Benzersiz Hasta Sayısı',
        '👨‍⚕️ Hekim Bazlı Hasta Sayıları': '👨‍⚕️ Hekim Bazlı Hasta Sayıları',
        'Hekim Bazlı Hasta Sayıları': 'Hekim Bazlı Hasta Sayıları',
        'Analiz İçin Hekim Seçiniz:': 'Analiz İçin Hekim Seçiniz:',
        '-- Hekim Seçin --': '-- Hekim Seçin --',
        'Hekim Toplam Kayıt': 'Hekim Toplam Kayıt',
        'Detaylarını görmek için lütfen yukarıdan bir hekim seçin.': 'Detaylarını görmek için lütfen yukarıdan bir hekim seçin.',
        '🤖 Akıllı Yorumlar': '🤖 Akıllı Yorumlar',
        'Gelir Analizi': 'Gelir Analizi',
        '💰 Kurum Gelir & Fatura Analizi & Kasa/Vezne Gelirleri': '💰 Kurum Gelir & Fatura Analizi & Kasa/Vezne Gelirleri',
        'Toplam Gelir': 'Toplam Gelir',
        'Toplam Fatura': 'Toplam Fatura',
        'Faturalandırılan Kişi': 'Faturalandırılan Kişi',
        'Vezne Geliri (Tahsilat)': 'Vezne Geliri (Tahsilat)',
        '🏥 Kurum Performansı': '🏥 Kurum Performansı',
        '📈 Gelir Trendi': '📈 Gelir Trendi',
        '📄 Fatura Listesi': '📄 Fatura Listesi',
        '🏦 Vezne': '🏦 Vezne',
        'Kurum Türüne Göre Gelir': 'Kurum Türüne Göre Gelir',
        'En Çok Ciro Yapan 10 Kurum/İlgili': 'En Çok Ciro Yapan 10 Kurum/İlgili',
        'Günlük Fatura Gelir Trendi': 'Günlük Fatura Gelir Trendi',
        '⬇️ Tüm Veriyi CSV Olarak İndir': '⬇️ Tüm Veriyi CSV Olarak İndir',
        'Son 500 Fatura Kaydı': 'Son 500 Fatura Kaydı',
        'Kasa Seç:': 'Kasa Seç:',
        'Kasa Hareketleri Dağılımı': 'Kasa Hareketleri Dağılımı',
        'Aylara Göre Tahsilat': 'Aylara Göre Tahsilat',
        'Hareket Türü Tanımlı Kasa Bilgileri': 'Hareket Türü Tanımlı Kasa Bilgileri',
        '🩻 Röntgen Branş ve Verimlilik Analiz Paneli': '🩻 Röntgen Branş ve Verimlilik Analiz Paneli',
        'Kurum Yapılan Tetkik': 'Kurum Yapılan Tetkik',
        'Adet': 'Adet',
        'Panoramik Tetkik': 'Panoramik Tetkik',
        'Periapikal Tetkik': 'Periapikal Tetkik',
        '👨‍⚕️ Hekim Analizi': '👨‍⚕️ Hekim Analizi',
        '🏥 Branş Analizi': '🏥 Branş Analizi',
        '🔥 Yoğunluk Haritası': '🔥 Yoğunluk Haritası',
        '📊 Verimlilik & Anomali': '📊 Verimlilik & Anomali',
        'Hekim Bazlı Tetkik Dağılımı': 'Hekim Bazlı Tetkik Dağılımı',
        'Hekim Bazlı Özet Tablo': 'Hekim Bazlı Özet Tablo',
        'Hekim': 'Hekim',
        'Toplam Film': 'Toplam Film',
        'Branş Bazlı Dağılım': 'Branş Bazlı Dağılım',
        'Tetkik Türü Dağılımı': 'Tetkik Türü Dağılımı',
        'Branş Bazlı Toplam Tetkik Hacmi': 'Branş Bazlı Toplam Tetkik Hacmi',
        'Hekim - Tetkik Türü Kullanım Yoğunluğu': 'Hekim - Tetkik Türü Kullanım Yoğunluğu',
        'Toplam': 'Toplam',
        'İleri Tetkik (Sefalometrik & Tomografi) Hekim Dağılımı': 'İleri Tetkik (Sefalometrik & Tomografi) Hekim Dağılımı',
        'Panoramik / Periapikal Tercih Dengesi': 'Panoramik / Periapikal Tercih Dengesi',
        'Hekim Hizmet Puan': 'Hekim Hizmet Puan',
        '🏥 Hekim Hizmet & Puan Analizi': '🏥 Hekim Hizmet & Puan Analizi',
        '⚠️ Seçilen tarih aralığında veri bulunamadı.': '⚠️ Seçilen tarih aralığında veri bulunamadı.',
        'Toplam Puan': 'Toplam Puan',
        'Gün': 'Gün',
        'Ort. Çalışma Günü': 'Ort. Çalışma Günü',
        'Kurum CMI (Ort.)': 'Kurum CMI (Ort.)',
        '📊 Finansal Performans Sıralaması': '📊 Finansal Performans Sıralaması',
        '📈 Pareto & CMI Analizi': '📈 Pareto & CMI Analizi',
        '🚀 Hizmet & Puan Analizi': '🚀 Hizmet & Puan Analizi',
        '📋 Detaylı Liste': '📋 Detaylı Liste',
        '🎯 Akıllı Kıyas & Risk Analizi': '🎯 Akıllı Kıyas & Risk Analizi',
        'SIRALAMA KRİTERİ': 'SIRALAMA KRİTERİ',
        '🏆 Toplam Puan': '🏆 Toplam Puan',
        '💰 Toplam Gelir': '💰 Toplam Gelir',
        '🎯 Hasta Başı Gelir': '🎯 Hasta Başı Gelir',
        'Hekim Sayısı': 'Hekim Sayısı',
        'Hekim Seçin:': 'Hekim Seçin:',
        'Çalışma Günü': 'Çalışma Günü',
        'Kurum Ort. Kıyas': 'Kurum Ort. Kıyas',
        'Hizmet Dağılımı': 'Hizmet Dağılımı',
        'TETKİK ADI': 'TETKİK ADI',
        'ADET': 'ADET',
        'TOPLAM PUAN': 'TOPLAM PUAN',
        'TOPLAM GELİR': 'TOPLAM GELİR',
        'DOKTOR ADI': 'DOKTOR ADI',
        'HASTA ADI SOYADI': 'HASTA ADI SOYADI',
        'TARİH': 'TARİH',
        'Risk ve Potansiyel Skorlama': 'Risk ve Potansiyel Skorlama',
        'Durum Analizi': 'Durum Analizi',
        'Karşılaştırmalı Veri Tablosu': 'Karşılaştırmalı Veri Tablosu',
        'Kurum Karar Destek Sistemi v2.0 | © 2026 | MetaSoft': 'Kurum Karar Destek Sistemi v2.0 | © 2026 | MetaSoft',
        'En Yüksek Toplam_Puan Üretenler': 'En Yüksek Toplam Puan Üretenler',
        'En Yüksek Toplam_Gelir Üretenler': 'En Yüksek Toplam Gelir Üretenler',
        'En Yüksek Hasta_Basi_Gelir Üretenler': 'En Yüksek Hasta Başı Gelir Üretenler',
        'En Düşük Toplam_Puan Üretenler': 'En Düşük Toplam Puan Üretenler',
        'En Düşük Toplam_Gelir Üretenler': 'En Düşük Toplam Gelir Üretenler',
        'En Düşük Toplam_Hasta Üretenler': 'En Düşük Toplam Hasta Üretenler',
        'Akran Grubu (Peer Group) Karşılaştırması': 'Akran Grubu (Peer Group) Karşılaştırması',
        'Kurum CMI Ortalaması': 'Kurum CMI Ortalaması',
        'NO_DATA_HEKIM': 'Hekim verisi bulunamadı.',
        'NO_DATA_HEAT': 'Seçilen aralıkta yoğunluk verisi bulunamadı.',
        'Hekim Bazlı Dağılım': 'Hekim Bazlı Dağılım',
        'Film Sayısı': 'Film Sayısı',
        'Panoramik / Periapikal Oran': 'Panoramik / Periapikal Oran',
        'Hekim Bazlı Tetkik Dağılımı': 'Hekim Bazlı Tetkik Dağılımı',
        'Hekim Bazlı Özet Tablo': 'Hekim Bazlı Özet Tablo',
        'Branş Bazlı Dağılım': 'Branş Bazlı Dağılım',
        'Tetkik Türü Dağılımı': 'Tetkik Türü Dağılımı',
        'Kasa Hareketleri Dağılımı': 'Kasa Hareketleri Dağılımı',
        'Vezne Kasası: Aylara Göre Tahsilat': 'Vezne Kasası: Aylara Göre Tahsilat',
        'Tahsilat': 'Tahsilat',
        'Kalan': 'Kalan',
        'İptal': 'İptal',
        'Kurum Türüne Göre Gelir': 'Kurum Türüne Göre Gelir',
        'En Çok Ciro Yapan 10 Kurum/İlgili': 'En Çok Ciro Yapan 10 Kurum/İlgili',
        'Günlük Fatura Gelir Trendi': 'Günlük Fatura Gelir Trendi',
        'En fazla tetkik işleyen hekim:': 'En fazla tetkik işleyen hekim:',
        'toplam': 'toplam',
        'film.': 'film.',
        'En düşük hacimli aktif hekim:': 'En düşük hacimli aktif hekim:',
        'Sistem Notu:': 'Sistem Notu:',
        'HASTA BAŞI GELİR': 'HASTA BAŞI GELİR',
        'Hasta Başı Gelir': 'Hasta Başı Gelir',
        'VEZNE KASASI': 'VEZNE KASASI',
        'VEZNE-1 KASASI': 'VEZNE-1 KASASI',
        'VEZNE-2 KASASI': 'VEZNE-2 KASASI',
        'PANORAMİK': 'PANORAMİK',
        'PERİAPİKAL': 'PERİAPİKAL',
        'SEFALOMETRİK': 'SEFALOMETRİK',
        'DENTAL TOMOGRAFİ': 'DENTAL TOMOGRAFİ',
        'PA PANORAMİK': 'PA PANORAMİK',
        'CEPHALOMETRİK': 'CEPHALOMETRİK',
        'Panoramik': 'Panoramik',
        'Periapikal': 'Periapikal',
        'Sefalometrik': 'Sefalometrik',
        'Dental Tomografi': 'Dental Tomografi',
        'Tahsilat': 'Tahsilat',
        'Kalan': 'Kalan',
        'İptal': 'İptal',
        'Toplam_Puan': 'Toplam_Puan',
        'Toplam_Gelir': 'Toplam_Gelir',
        'Hasta_Basi_Gelir': 'Hasta_Basi_Gelir',
        'Toplam_Hasta': 'Toplam_Hasta',
        'TETKİK_ADI': 'TETKİK_ADI',
        'ADET': 'ADET',
        'TETKIK_ADI': 'TETKIK_ADI',
        'Kümülatif %': 'Kümülatif %',
        'Grafik için fatura verisi bulunamadı.': 'Grafik için fatura verisi bulunamadı.',
        'En Düşük Hasta_Basi_Gelir Üretenler': 'En Düşük Hasta_Basi_Gelir Üretenler',
        'En Yüksek Hasta_Basi_Gelir Üretenler': 'En Yüksek Hasta_Basi_Gelir Üretenler',
        'Randevu Analizi': 'Randevu Analizi',
        'Hekim Randevu & Sadakat Analizi': '📅 Hekim Randevu & Sadakat Analizi',
        'Genel Sadakat Oranı': 'Genel Sadakat Oranı',
        'Hizmete Dönüşen': 'Hizmete Dönüşen',
        'Aktif Hekim Sayısı': 'Aktif Hekim Sayısı',
        'Hekim Performansı': '📊 Hekim Performansı',
        'Kanal & Poliklinik': '📍 Kanal & Poliklinik',
        'Akıllı Yorumlar': '💡 Akıllı Yorumlar',
        'Grafik için Hekim Sayısı:': 'Grafik için Hekim Sayısı:',
        'Sadakat Oranı En Yüksek': 'Sadakat Oranı En Yüksek',
        'En Yoğun 10 Poliklinik': 'En Yoğun 10 Poliklinik',
        'Randevu Kanalları': 'Randevu Kanalları',
        '⚙️ Operasyonel İçgörüler': '⚙️ Operasyonel İçgörüler',
        'Yabancı Hasta': 'Yabancı Hasta',
        '🌍 Yabancı Hasta Analizi': '🌍 Yabancı Hasta Analizi',
        'Toplam Yabancı Hasta': 'Toplam Yabancı Hasta',
        'Hasta Başı Ort. Gelir': 'Hasta Başı Ort. Gelir',
        'Ülke Çeşitliliği': 'Ülke Çeşitliliği',
        '📍 Coğrafi Dağılım': '📍 Coğrafi Dağılım',
        'Verimlilik Matrisi': '📈 Verimlilik Matrisi',
        'Demografi': '👥 Demografi',
        'Gelir Lideri Ülkeler': 'Gelir Lideri Ülkeler',
        'Hasta Sayısı Dağılımı': 'Hasta Sayısı Dağılımı',
        'Ülke Bazlı Verimlilik (Hacim vs. Değer)': 'Ülke Bazlı Verimlilik (Hacim vs. Değer)',
        'Ülkeler hasta başı gelir ve toplam gelir birlikte değerlendirilerek sıralanmıştır.': 'Ülkeler hasta başı gelir ve toplam gelir birlikte değerlendirilerek sıralanmıştır.',
        'Ülke': 'Ülke',
        'Hasta Sayısı': 'Hasta Sayısı',
        'Hacim / Değer': 'Hacim / Değer',
        'Yorum': 'Yorum',
        'Verimlilik tablosu için veri bulunamadı.': 'Verimlilik tablosu için veri bulunamadı.',
        'Yaş ve Cinsiyet Dağılımı': 'Yaş ve Cinsiyet Dağılımı',
        'Yaş grupları benzersiz hasta sayısına göre ve cinsiyet kırılımı ile listelenmiştir.': 'Yaş grupları benzersiz hasta sayısına göre ve cinsiyet kırılımı ile listelenmiştir.',
        'Yaş Grubu': 'Yaş Grubu',
        'Cinsiyet Dağılımı': 'Cinsiyet Dağılımı',
        'Yoğunluk': 'Yoğunluk',
        'Cinsiyet Payı': 'Cinsiyet Payı',
        '🤖 Akıllı Analiz Notları': '🤖 Akıllı Analiz Notları',
        'İlk 3 ülke toplam gelirin': 'İlk 3 ülke toplam gelirin',
        'oluşturuyor.': 'oluşturuyor.',
        'Sevk Analizi': 'Sevk Analizi',
        'Hekim Sevk & Akıllı Karar Destek': '🩺 Hekim Sevk & Akıllı Karar Destek',
        'Toplam Sevk': 'Toplam Sevk',
        'Genel Sevk Oranı': 'Genel Sevk Oranı',
        'Genel Trafik': '📊 Genel Trafik',
        'Sevk Oranları': '📈 Sevk Oranları',
        'Hekim-Branş Eşleşmesi': '🧩 Hekim-Branş Eşleşmesi',
        'Eşleşmeler': '🔗 Eşleşmeler',
        'Hekim Detaylı Arama': '🔍 Hekim Detaylı Arama',
        'Ham Veri': '📄 Ham Veri',
        'Hekim Sayısı:': 'Hekim Sayısı:',
        'En Çok Sevk Yapanlar': 'En Çok Sevk Yapanlar',
        'En Çok Sevk Kabul Edenler': 'En Çok Sevk Kabul Edenler',
        'Hekim Bazlı Sevk Verimliliği': 'Hekim Bazlı Sevk Verimliliği',
        'En yüksek sevk oranına sahip ilk 30 hekim, hasta ve sevk hacmi ile birlikte listelenmiştir.': 'En yüksek sevk oranına sahip ilk 30 hekim, hasta ve sevk hacmi ile birlikte listelenmiştir.',
        'Oran (%)': 'Oran (%)',
        'Gorsel': 'Görsel',
        'Durum': 'Durum',
        'Sevk verimliligi icin veri bulunamadi.': 'Sevk verimliliği için veri bulunamadı.',
        'Sevk Oran Tablosu': 'Sevk Oran Tablosu',
        'Servisler Arası Sevk Trafiği': 'Servisler Arası Sevk Trafiği',
        'En Yoğun 10 Akış': 'En Yoğun 10 Akış',
        'Kaynak': 'Kaynak',
        'Hedef': 'Hedef',
        'Hekimlerin Hedef Branş Dağılımı': 'Hekimlerin Hedef Branş Dağılımı',
        'Hekimlerin \'Favori\' Sevk Branşları': 'Hekimlerin \'Favori\' Sevk Branşları',
        'En Çok Sevk Branş': 'En Çok Sevk Branş',
        'Kritik Konsültasyon Kanalları': 'Kritik Konsültasyon Kanalları',
        'Sevk analizi için hekim seçiniz:': 'Sevk analizi için hekim seçiniz:',
        'Sevk Oranı': 'Sevk Oranı',
        'Hekim Sevk Dağılımı': 'Hekim Sevk Dağılımı',
        'Hekimin Tercih Ettiği Branşlar': 'Hekimin Tercih Ettiği Branşlar',
        'Kabul Eden Hekimler': 'Kabul Eden Hekimler',
        'Seçilen hekim için sevk kaydı bulunamadı.': 'Seçilen hekim için sevk kaydı bulunamadı.',
        'Ham Sevk Verisi (İlk 500 Kayıt)': 'Ham Sevk Verisi (İlk 500 Kayıt)',
        'Ana Sayfa': 'Ana Sayfa',
        'Poliklinik Hasta': 'Poliklinik Hasta',
        'Ad': 'Ad',
        'Toplam': 'Toplam',
        'Hekim Toplam Kayıt': 'Hekim Toplam Kayıt',
        'Branş Sayısı': 'Branş Sayısı',
        'Personel Sorgulama': 'Personel Sorgulama',
        'Personel Sorgulama Analiz Paneli': 'Personel Sorgulama Analiz Paneli',
        'Çalışma Durumu': 'Çalışma Durumu',
        'Kadro Unvanı': 'Kadro Unvanı',
        'Personel Türü': 'Personel Türü',
        'Hizmet Sınıfı': 'Hizmet Sınıfı',
        'Tümünü Gör': 'Tümünü Gör',
        'Personel Listesi': 'Personel Listesi',
        'Arama yapın...': 'Arama yapın...',
        'Filtreyi Temizle': 'Filtreyi Temizle',
        'Personel Adı': 'Personel Adı',
        'Görev Kurumu': 'Görev Kurumu',
        'Unvan (Görev)': 'Unvan (Görev)',
        'Toplam Kayıt:': 'Toplam Kayıt:',
        'Toplam Tür:': 'Toplam Tür:',
        'Toplam Sınıf:': 'Toplam Sınıf:',
        'Çalışma Türü': 'Çalışma Türü',
        'Aradığınız kriterlere uygun personel bulunamadı.': 'Aradığınız kriterlere uygun personel bulunamadı.',
        'Lütfen filtrelerinizi kontrol edin veya arama terimini değiştirin.': 'Lütfen filtrelerinizi kontrol edin veya arama terimini değiştirin.',
        'Çalışma Durumu Analizi': 'Çalışma Durumu Analizi',
        'Kadro Unvan Dağılımı': 'Kadro Unvan Dağılımı',
        'Personel Tür Analizi': 'Personel Tür Analizi',
        'Hizmet Sınıfı Dağılımı': 'Hizmet Sınıfı Dağılımı',
        '📋 Çalışma Durumu': '📋 Çalışma Durumu',
        '🏷️ Kadro Unvanı': '🏷️ Kadro Unvanı',
        '👥 Personel Türü': '👥 Personel Türü',
        '🏢 Hizmet Sınıfı': '🏢 Hizmet Sınıfı',
        '📈 Seçilen Kategori Grafiği': '📈 Seçilen Kategori Grafiği',
        '📄 PERSONEL DETAY LİSTESİ': '📄 PERSONEL DETAY LİSTESİ',
        '(Tüm Personel)': '(Tüm Personel)',
        '(Tümünü Gör)': '(Tümünü Gör)',
        'İsim veya Kurum ara...': 'İsim veya Kurum ara...',
        'Temizle': 'Temizle',
        'Personel Adı': 'Personel Adı',
        'Görev Kurumu': 'Görev Kurumu',
        'Durum': 'Durum',
        'Unvan (Görev)': 'Unvan (Görev)',
        'Toplam Unvan:': 'Toplam Unvan:',
        'Toplam Tür:': 'Toplam Tür:',
        'Toplam Sınıf:': 'Toplam Sınıf:',
        'Çalışma Türü': 'Çalışma Türü',
        '📊 Personel Türü': '📊 Personel Türü',
        'ÇALIŞIYOR': 'ÇALIŞIYOR',
        'İZİNLİ': 'İZİNLİ',
        'RAPORLU': 'RAPORLU',
        'GÖREVLENDİRME': 'GÖREVLENDİRME'
    },
    'en': {
        'Kurum Performans Yönetim Sistemi': 'Institution Performance<br>Management System',
        'Dashboard': 'Dashboard',
        'ANA MODÜLLER': 'MAIN MODULES',
        'Ana Sayfa': 'Home',
        'Hekim Hizmet Puan Analiz': 'MD Service Point Analysis',
        'Hekim Poliklinik Hasta': 'MD Polyclinic Patient',
        'Tedavi Grupları Analizi': 'Treatment Groups Analysis',
        'Kurum Malzeme Tüketim': 'Material Consumption',
        'Yabancı Hasta Analizi': 'Foreign Patient Analysis',
        'Hekim Randevu Analizi': 'MD Appointment Analysis',
        'Kurum Gelir Analiz': 'Institution Income Analysis',
        'Sterilizasyon Maliyet': 'Sterilization Cost',
        'Ameliyat Kar-Zarar': 'Surgery Profit-Loss',
        'Röntgen Analizleri': 'X-Ray Analysis',
        'Fatura Analiz': 'Invoice Analysis',
        'Vezne Gelir Analiz': 'Cashier Income Analysis',
        'Ayaktan/Yatan Doluluk': 'Outpatient/Inpatient Occupancy',
        'Hekim Sevk Sayıları': 'Physician Referral Counts',
        'YARDIMCI MODÜLLER': 'SUPPORT MODULES',
        'DİĞER': 'OTHER',
        'Tıbbi Atık Analizi': 'Medical Waste Analysis',
        'Protez Analizi': 'Prosthesis Analysis',
        'Röntgen Analizizi': 'X-Ray Analysis',
        'Koyu': 'Dark',
        'Açık': 'Light',
        'Filtrele': '🔄 Filter',
        'Çıkış': '🚪 Logout',
        'Yükleniyor, lütfen bekleyin...': 'Loading, please wait...',
        'Günaydın': 'Good Morning',
        'İyi Günler': 'Good Day',
        'İyi Akşamlar': 'Good Evening',
        'Analiz periyodu': 'Analysis period',
        '🚀 Finansal Performans Özeti': '🚀 Financial Performance Summary',
        'Toplam Hasta': 'Total Patients',
        'Kişi': 'People',
        'Güncel Kayıt': 'Live Records',
        'Tahmini Toplam Gelir': 'Est. Total Income',
        'Tahakkuk Eden': 'Accrued',
        'Hasta Başına Düşen Ortalama Gelir': 'Average Income Per Patient',
        'Verimlilik': 'Efficiency',
        'Sistem Notu': 'System Note',
        'Veriler, seçili tarih aralığındaki güncel (canlı) hareketlerden konsolide edilmiştir.': 'Data is consolidated from live movements within the selected date range.',
        '🛠️ Sistem Sağlık Durumu': '🛠️ System Health Status',
        'Sunucu Bağlantısı': 'Server Connection',
        '✅ Doğrulandı': '✅ Verified',
        '❌ Bağlantı Yok': '❌ No Connection',
        'Sorgu Performance': 'Query Performance',
        'sn': 'sec',
        'Ölçülmedi': 'Not Measured',
        'Son Güncelleme': 'Last Update',
        'Bugün': 'Today',
        'Dün': 'Yesterday',
        'Son 7 Gün': 'Last 7 Days',
        'Son 30 Gün': 'Last 30 Days',
        'Bu Ay': 'This Month',
        'Geçen Ay': 'Last Month',
        'Bu Yıl': 'This Year',
        'Geçen Yıl': 'Last Year',
        'Özel': 'Custom',
        'Aktif Dönem': 'Active Period',
        'Hekim Poliklinik Hasta Analizi': 'MD Polyclinic Patient Analysis',
        'Toplam Kayıt': 'Total Records',
        'Benzersiz Hasta': 'Unique Patients',
        'Aktif Hekim': 'Active Physicians',
        'Branş Sayısı': 'Number of Specialties',
        '📊 Performans (Sıralama Kriterli)': '📊 Performance (by Ranking Criteria)',
        '📈 Kurum & Trend': '📈 Institution & Trend',
        '🔥 Yoğunluk Analizi': '🔥 Density Analysis',
        '🔍 Hekim Detay': '🔍 MD Detail',
        'SIRALAMA KRİTERİ:': 'SORTING CRITERIA:',
        '📋 Kayıt Sayısı': '📋 Total Records',
        '👥 Benzersiz Hasta Sayısı': '👥 Unique Patient Count',
        '👨‍⚕️ Hekim Bazlı Hasta Sayıları': '👨‍⚕️ MD-Based Patient Counts',
        'Hekim Bazlı Hasta Sayıları': 'MD-Based Patient Counts',
        'Analiz İçin Hekim Seçiniz:': 'Select Physician for Analysis:',
        '-- Hekim Seçin --': '-- Select Physician --',
        'Hekim Toplam Kayıt': 'Physician Total Records',
        'Detaylarını görmek için lütfen yukarıdan bir hekim seçin.': 'Please select a physician above to see details.',
        '🤖 Akıllı Yorumlar': '🤖 Smart Insights',
        'Gelir Analizi': 'Revenue Analysis',
        '💰 Kurum Gelir & Fatura Analizi & Kasa/Vezne Gelirleri': '💰 Institution Revenue & Invoice Analysis & Cashier Income',
        'Toplam Gelir': 'Total Revenue',
        'Toplam Fatura': 'Total Invoices',
        'Faturalandırılan Kişi': 'Invoiced Persons',
        'Vezne Geliri (Tahsilat)': 'Cashier Income (Collection)',
        '🏥 Kurum Performansı': '🏥 Institution Performance',
        '📈 Gelir Trendi': '📈 Revenue Trend',
        '📄 Fatura Listesi': '📄 Invoice List',
        '🏦 Vezne': '🏦 Cashier',
        'Kurum Türüne Göre Gelir': 'Revenue by Institution Type',
        'En Çok Ciro Yapan 10 Kurum/İlgili': 'Top 10 Revenue-Generating Institutions',
        'Günlük Fatura Gelir Trendi': 'Daily Invoice Revenue Trend',
        '⬇️ Tüm Veriyi CSV Olarak İndir': '⬇️ Download All Data as CSV',
        'Son 500 Fatura Kaydı': 'Last 500 Invoice Records',
        'Kasa Seç:': 'Select Cashier Box:',
        'Kasa Hareketleri Dağılımı': 'Cashier Activity Distribution',
        'Aylara Göre Tahsilat': 'Collections by Month',
        'Hareket Türü Tanımlı Kasa Bilgileri': 'Cashier Info by Activity Type',
        '🩻 Röntgen Branş ve Verimlilik Analiz Paneli': '🩻 X-Ray Specialty and Efficiency Analysis Panel',
        'Kurum Yapılan Tetkik': 'Institution Procedures',
        'Adet': 'Units',
        'Panoramik Tetkik': 'Panoramic Procedures',
        'Periapikal Tetkik': 'Periapical Procedures',
        '👨‍⚕️ Hekim Analizi': '👨‍⚕️ Physician Analysis',
        '🏥 Branş Analizi': '🏥 Specialty Analysis',
        '🔥 Yoğunluk Haritası': '🔥 Heatmap',
        '📊 Verimlilik & Anomali': '📊 Efficiency & Anomaly',
        'Hekim Bazlı Tetkik Dağılımı': 'Procedure Distribution by Physician',
        'Hekim Bazlı Özet Tablo': 'Summary Table by Physician',
        'Hekim': 'Physician',
        'Toplam Film': 'Total Films',
        'Branş Bazlı Dağılım': 'Distribution by Specialty',
        'Tetkik Türü Dağılımı': 'Procedure Type Distribution',
        'Branş Bazlı Toplam Tetkik Hacmi': 'Total Procedure Volume by Specialty',
        'Hekim - Tetkik Türü Kullanım Yoğunluğu': 'Physician - Procedure Type Usage Density',
        'Toplam': 'Total',
        'İleri Tetkik (Sefalometrik & Tomografi) Hekim Dağılımı': 'Advanced Procedure (Cephalometric & Tomography) MD Distribution',
        'Panoramik / Periapikal Tercih Dengesi': 'Panoramic / Periapical Preference Balance',
        'Hekim Hizmet Puan': 'Physician Service Points',
        '🏥 Hekim Hizmet & Puan Analizi': '🏥 Physician Service & Point Analysis',
        '⚠️ Seçilen tarih aralığında veri bulunamadı.': '⚠️ No data found for the selected date range.',
        'Toplam Puan': 'Total Points',
        'Gün': 'Days',
        'Ort. Çalışma Günü': 'Avg. Working Days',
        'Kurum CMI (Ort.)': 'Institution CMI (Avg.)',
        '📊 Finansal Performans Sıralaması': '📊 Financial Performance Ranking',
        '📈 Pareto & CMI Analizi': '📈 Pareto & CMI Analysis',
        '🚀 Hizmet & Puan Analizi': '🚀 Service & Point Analysis',
        '📋 Detaylı Liste': '📋 Detailed List',
        '🎯 Akıllı Kıyas & Risk Analizi': '🎯 Smart Benchmark & Risk Analysis',
        'SIRALAMA KRİTERİ': 'RANKING CRITERIA',
        '🏆 Toplam Puan': '🏆 Total Points',
        '💰 Toplam Gelir': '💰 Total Revenue',
        '🎯 Hasta Başı Gelir': '🎯 Revenue Per Patient',
        'Hekim Sayısı': 'Physician Count',
        'Hekim Seçin:': 'Select Physician:',
        'Çalışma Günü': 'Working Days',
        'Kurum Ort. Kıyas': 'Inst. Avg. Benchmark',
        'Hizmet Dağılımı': 'Service Distribution',
        'TETKİK ADI': 'PROCEDURE NAME',
        'ADET': 'COUNT',
        'TOPLAM PUAN': 'TOTAL POINTS',
        'TOPLAM GELİR': 'TOTAL REVENUE',
        'DOKTOR ADI': 'PHYSICIAN NAME',
        'HASTA ADI SOYADI': 'PATIENT NAME SURNAME',
        'TARİH': 'DATE',
        'Risk ve Potansiyel Skorlama': 'Risk and Potential Scoring',
        'Durum Analizi': 'Status Analysis',
        'Karşılaştırmalı Veri Tablosu': 'Comparative Data Table',
        'Kurum Karar Destek Sistemi v2.0 | © 2026 | MetaSoft': 'Institution Decision Support System v2.0 | © 2026 | MetaSoft',
        'En Yüksek Toplam_Puan Üretenler': 'Top Producers by Points',
        'En Yüksek Toplam_Gelir Üretenler': 'Top Producers by Revenue',
        'En Yüksek Hasta_Basi_Gelir Üretenler': 'Top Producers by Revenue Per Patient',
        'En Düşük Toplam_Puan Üretenler': 'Bottom Producers by Points',
        'En Düşük Toplam_Gelir Üretenler': 'Bottom Producers by Revenue',
        'En Düşük Toplam_Hasta Üretenler': 'Bottom Producers by Patient Count',
        'Akran Grubu (Peer Group) Karşılaştırması': 'Peer Group Comparison',
        'Kurum CMI Ortalaması': 'Institution CMI Average',
        'NO_DATA_HEKIM': 'Physician data not found.',
        'NO_DATA_HEAT': 'Density data not found for the selected range.',
        'Hekim Bazlı Dağılım': 'Physician-Based Distribution',
        'Film Sayısı': 'Film Count',
        'Panoramik / Periapikal Oran': 'Panoramic / Periapical Ratio',
        'Hekim Bazlı Tetkik Dağılımı': 'Physician-Based Exam Distribution',
        'Hekim Bazlı Özet Tablo': 'Physician-Based Summary Table',
        'Branş Bazlı Dağılım': 'Specialty-Based Distribution',
        'Tetkik Türü Dağılımı': 'Exam Type Distribution',
        'Kasa Hareketleri Dağılımı': 'Cashier Movement Distribution',
        'Vezne Kasası: Aylara Göre Tahsilat': 'Monthly Collection Trend',
        'Tahsilat': 'Collection',
        'Kalan': 'Balance',
        'İptal': 'Canceled',
        'Kurum Türüne Göre Gelir': 'Revenue by Institution Type',
        'En Çok Ciro Yapan 10 Kurum/İlgili': 'Top 10 Revenue-Generating Institutions',
        'Günlük Fatura Gelir Trendi': 'Daily Invoice Revenue Trend',
        'En fazla tetkik işleyen hekim:': 'Highest volume physician:',
        'toplam': 'total',
        'film.': 'films.',
        'En düşük hacimli aktif hekim:': 'Lowest volume active physician:',
        'Sistem Notu:': 'System Note:',
        'Veriler, seçili tarih aralığındaki güncel (canlı) hareketlerden konsolide edilmiştir.': 'Data is consolidated from live movements within the selected date range.',
        'Premium Hizmet Üretimi': 'Premium Service Production',
        'Düşük CMI Riski': 'Low CMI Risk',
        'Dengeli': 'Balanced',
        'Hizmet Dağılımı': 'Service Distribution',
        'Kayıt': 'Records',
        'Kurum Ort.': 'Inst. Avg.',
        'HASTA BAŞI GELİR': 'REVENUE PER PATIENT',
        'Hasta Başı Gelir': 'Revenue Per Patient',
        'VEZNE KASASI': 'CASHIER ACCOUNT',
        'VEZNE-1 KASASI': 'CASHIER ACCOUNT - 1',
        'VEZNE-2 KASASI': 'CASHIER ACCOUNT - 2',
        'PANORAMİK': 'PANORAMIC',
        'PERİAPİKAL': 'PERIAPICAL',
        'SEFALOMETRİK': 'CEPHALOMETRIC',
        'DENTAL TOMOGRAFİ': 'DENTAL CT',
        'PA PANORAMİK': 'PA PANORAMIC',
        'CEPHALOMETRİK': 'CEPHALOMETRIC',
        'Panoramik': 'Panoramic',
        'Periapikal': 'Peri-apical',
        'Sefalometrik': 'Cephalometric',
        'Dental Tomografi': 'Dental CT',
        'Tahsilat': 'Collection',
        'Kalan': 'Balance',
        'İptal': 'Canceled',
        'Toplam_Puan': 'Total Points',
        'Toplam_Gelir': 'Total Revenue',
        'Hasta_Basi_Gelir': 'Revenue Per Patient',
        'Toplam_Hasta': 'Total Patients',
        'TETKİK_ADI': 'PROCEDURE NAME',
        'ADET': 'COUNT',
        'TETKIK_ADI': 'PROCEDURE NAME',
        'Kümülatif %': 'Cumulative %',
        'Grafik için fatura verisi bulunamadı.': 'No data found for the chart.',
        'En Düşük Hasta_Basi_Gelir Üretenler': 'Bottom Producers by Revenue Per Patient',
        'En Yüksek Hasta_Basi_Gelir Üretenler': 'Top Producers by Revenue Per Patient',
        'Randevu Analizi': 'Appointment Analysis',
        'Hekim Randevu & Sadakat Analizi': '📅 Physician Appointment & Loyalty Analysis',
        'Genel Sadakat Oranı': 'General Loyalty Rate',
        'Hizmete Dönüşen': 'Converted to Service',
        'Aktif Hekim Sayısı': 'Active Physician Count',
        'Hekim Performansı': '📊 Physician Performance',
        'Kanal & Poliklinik': '📍 Channel & Polyclinic',
        'Akıllı Yorumlar': '💡 Smart Insights',
        'Grafik için Hekim Sayısı:': 'Number of Physicians for Chart:',
        'Sadakat Oranı En Yüksek': 'Top Physicians by Loyalty Rate',
        'En Yoğun 10 Poliklinik': 'Top 10 Busiest Polyclinics',
        'Randevu Kanalları': 'Appointment Channels',
        '⚙️ Operasyonel İçgörüler': '⚙️ Operational Insights',
        'Yabancı Hasta': 'Foreign Patient',
        '🌍 Yabancı Hasta Analizi': '🌍 Foreign Patient Analysis',
        'Toplam Yabancı Hasta': 'Total Foreign Patients',
        'Hasta Başı Ort. Gelir': 'Avg. Revenue Per Patient',
        'Ülke Çeşitliliği': 'Country Diversity',
        '📍 Coğrafi Dağılım': '📍 Geographic Distribution',
        'Verimlilik Matrisi': '📈 Efficiency Matrix',
        'Demografi': '👥 Demography',
        'Gelir Lideri Ülkeler': 'Top Revenue-Generating Countries',
        'Hasta Sayısı Dağılımı': 'Patient Count Distribution',
        'Ülke Bazlı Verimlilik (Hacim vs. Değer)': 'Country-Based Efficiency (Volume vs. Value)',
        'Ülkeler hasta başı gelir ve toplam gelir birlikte değerlendirilerek sıralanmıştır.': 'Countries are ranked by evaluating revenue per patient and total revenue together.',
        'Ülke': 'Country',
        'Hasta Sayısı': 'Patient Count',
        'Hacim / Değer': 'Volume / Value',
        'Yorum': 'Comment',
        'Verimlilik tablosu için veri bulunamadı.': 'No data found for efficiency table.',
        'Yaş ve Cinsiyet Dağılımı': 'Age and Gender Distribution',
        'Yaş grupları benzersiz hasta sayısına göre ve cinsiyet kırılımı ile listelenmiştir.': 'Age groups are listed by unique patient count and gender breakdown.',
        'Yaş Grubu': 'Age Group',
        'Cinsiyet Dağılımı': 'Gender Distribution',
        'Yoğunluk': 'Density',
        'Cinsiyet Payı': 'Gender Share',
        '🤖 Akıllı Analiz Notları': '🤖 Smart Analysis Notes',
        'İlk 3 ülke toplam gelirin': 'The top 3 countries account for',
        'oluşturuyor.': 'of total revenue.',
        'Sevk Analizi': 'Referral Analysis',
        'Hekim Sevk & Akıllı Karar Destek': '🩺 Physician Referral & Smart Decision Support',
        'Toplam Sevk': 'Total Referrals',
        'Genel Sevk Oranı': 'General Referral Rate',
        'Genel Trafik': '📊 General Traffic',
        'Sevk Oranları': '📈 Referral Rates',
        'Hekim-Branş Eşleşmesi': '🧩 Physician-Specialty Mapping',
        'Eşleşmeler': '🔗 Mappings',
        'Hekim Detaylı Arama': '🔍 Physician Detailed Search',
        'Ham Veri': '📄 Raw Data',
        'Hekim Sayısı:': 'Physician Count:',
        'En Çok Sevk Yapanlar': 'Top Senders',
        'En Çok Sevk Kabul Edenler': 'Top Receivers',
        'Hekim Bazlı Sevk Verimliliği': 'Physician-Based Referral Efficiency',
        'En yüksek sevk oranına sahip ilk 30 hekim, hasta ve sevk hacmi ile birlikte listelenmiştir.': 'The top 30 physicians with the highest referral rates are listed with patient and referral volumes.',
        'Oran (%)': 'Rate (%)',
        'Gorsel': 'Visual',
        'Durum': 'Status',
        'Sevk verimliligi icin veri bulunamadi.': 'No data found for referral efficiency.',
        'Sevk Oran Tablosu': 'Referral Rate Table',
        'Servisler Arası Sevk Trafiği': 'Inter-Service Referral Traffic',
        'En Yoğun 10 Akış': 'Top 10 Busiest Flows',
        'Kaynak': 'Source',
        'Hedef': 'Target',
        'Hekimlerin Hedef Branş Dağılımı': 'Physician Target Specialty Distribution',
        'Hekimlerin \'Favori\' Sevk Branşları': 'Physicians\' \'Favorite\' Referral Specialties',
        'En Çok Sevk Branş': 'Top Referral Specialty',
        'Kritik Konsültasyon Kanalları': 'Critical Consultation Channels',
        'Sevk analizi için hekim seçiniz:': 'Select physician for referral analysis:',
        'Sevk Oranı': 'Referral Rate',
        'Hekim Sevk Dağılımı': 'Physician Referral Distribution',
        'Hekimin Tercih Ettiği Branşlar': 'Physicians\' Preferred Specialties',
        'Kabul Eden Hekimler': 'Receiving Physicians',
        'Seçilen hekim için sevk kaydı bulunamadı.': 'No referral record found for the selected physician.',
        'Ham Sevk Verisi (İlk 500 Kayıt)': 'Raw Referral Data (First 500 Records)',
        'Ana Sayfa': 'Home',
        'Poliklinik Hasta': 'Polyclinic Patient',
        'Ad': 'Name',
        'Toplam': 'Total',
        'Hekim Toplam Kayıt': 'Physician Total Records',
        'Branş Sayısı': 'Number of Specialties',
        'Tedavi Grupları': 'Treatment Groups',
        'Tedavi Grupları Analizi': 'Treatment Groups Analysis',
        'Grup Sayısı': 'Group Count',
        'İşlem Hacmi': 'Procedure Volume',
        '📊 Performans Kıyaslama': '📊 Performance Comparison',
        '🔍 Grup Detayları': '🔍 Group Details',
        'Gösterilecek Grup Sayısı': 'Number of Groups to Show',
        'Gelire Göre Top': 'Top by Revenue',
        'İşleme Göre Top': 'Top by Procedure',
        '💡 Verimlilik Analizi (Birim Başı Gelir)': '💡 Efficiency Analysis (Revenue Per Unit)',
        '🎯 Sistem Analizi': '🎯 System Analysis',
        'Detaylı incelemek için bir grup seçin:': 'Select a group to examine in detail:',
        'İşlem Adedi': 'Procedure Count',
        'Seçili grup için detay bulunamadı.': 'No details found for the selected group.',
        'Protez Süreç Performansı': 'Prosthesis Process Performance',
        '🦷 Protez Süreç Performans Paneli': '🦷 Prosthesis Process Performance Panel',
        'Filtrelenen Vaka': 'Filtered Cases',
        'Gecikme Oranı': 'Delay Rate',
        'Geciken Vaka': 'Delayed Cases',
        'Ort. Teslimat': 'Avg. Delivery',
        '📊 Genel Performans': '📊 General Performance',
        '📍 Geciken Hekim Listesi': '📍 Delayed Physician List',
        '🧾 Hasta Detayları': '🧾 Patient Details',
        '📈 Trend Analizi': '📈 Trend Analysis',
        '🔍 Analiz Ayarları': '🔍 Analysis Settings',
        'Kritik Gün Eşiği': 'Critical Day Threshold',
        'Gösterilecek Hekim Sayısı': 'Number of Physicians to Show',
        'Hekim Bazlı Süre (Hedef vs Gerçek)': 'Physician-Based Time (Target vs Actual)',
        'En Çok Geciken 10 İşlem (Ort. Gün)': 'Top 10 Delayed Procedures (Avg. Days)',
        '⚠️ Kritik Sınırı (30 Gün) Aşan Vakalar': '⚠️ Cases Exceeding Critical Limit (30 Days)',
        'Kritik Vaka Sayısı': 'Critical Case Count',
        'Ort. Teslim Süresi': 'Avg. Delivery Time',
        'Toplam Gecikme (Gün)': 'Total Delay (Days)',
        'Hekim ve Hasta Bazlı Detay Sorgulama': 'Physician and Patient Based Detail Query',
        'Sadece gecikenleri göster': 'Show only delayed',
        'Haftalık / Aylık Ortalama Gecikme Trendi': 'Weekly / Monthly Average Delay Trend',
        'Stratejik Analiz Özeti': 'Strategic Analysis Summary',
        'Gün': 'Days',
        'Malzeme Tüketim': 'Material Consumption',
        '📦 Kurum Malzeme Tüketim Analizi': '📦 Institution Material Consumption Analysis',
        'Toplam Tüketim (Adet)': 'Total Consumption (Units)',
        'Farklı Malzeme': 'Distinct Materials',
        'Sterilizasyon': 'Sterilization',
        '💉 Sterilizasyon Maliyet Analizi': '💉 Sterilization Cost Analysis',
        'Toplam Maliyet': 'Total Cost',
        'Toplam Paket': 'Total Packages',
        'Tıbbi Atık': 'Medical Waste',
        '⚗️ Tıbbi Atık Analizi': '⚗️ Medical Waste Analysis',
        'Toplam Atık': 'Total Waste',
        'Aylık Ortalama': 'Monthly Average',
        'Birim Sayısı': 'Number of Units',
        'İŞLEM ADEDİ': 'PROCEDURE COUNT',
        'TOPLAM CİRO': 'TOTAL REVENUE',
        'TETKİK ADI': 'PROCEDURE NAME',
        'HASTA ADI SOYADI': 'PATIENT NAME SURNAME',
        'Personel Sorgulama': 'Personnel Inquiry',
        'Personel Sorgulama Analiz Paneli': 'Personnel Inquiry & Analysis Panel',
        'Çalışma Durumu': 'Work Status',
        'Kadro Unvanı': 'Staff Title',
        'Personel Türü': 'Personnel Type',
        'Hizmet Sınıfı': 'Service Class',
        'Tümünü Gör': 'View All',
        'Personel Listesi': 'Personnel List',
        'Arama yapın...': 'Search...',
        'Filtreyi Temizle': 'Clear Filter',
        'Toplam Kayıt:': 'Total Records:',
        'Toplam Tür:': 'Total Types:',
        'Toplam Sınıf:': 'Total Classes:',
        'Çalışma Türü': 'Work Type',
        'Aradığınız kriterlere uygun personel bulunamadı.': 'No personnel found matching your criteria.',
        'Lütfen filtrelerinizi kontrol edin veya arama terimini değiştirin.': 'Please check your filters or change your search term.',
        'Çalışma Durumu Analizi': 'Work Status Analysis',
        'Kadro Unvan Dağılımı': 'Staff Title Distribution',
        'Personel Tür Analizi': 'Personnel Type Analysis',
        'Hizmet Sınıfı Dağılımı': 'Service Class Distribution',
        '📋 Çalışma Durumu': '📋 Work Status',
        '🏷️ Kadro Unvanı': '🏷️ Staff Title',
        '👥 Personel Türü': '👥 Personnel Type',
        '🏢 Hizmet Sınıfı': '🏢 Service Class',
        '📈 Seçilen Kategori Grafiği': '📈 Category Analysis Chart',
        '📄 PERSONEL DETAY LİSTESİ': '📄 PERSONNEL DETAIL LIST',
        '(Tüm Personel)': '(All Personnel)',
        '(Tümünü Gör)': '(View All)',
        'İsim veya Kurum ara...': 'Search by name or institution...',
        'Temizle': 'Clear',
        'Personel Adı': 'Personnel Name',
        'Görev Kurumu': 'Duty Institution',
        'Durum': 'Status',
        'Unvan (Görev)': 'Title (Duty)',
        'Toplam Unvan:': 'Total Titles:',
        'ÇALIŞIYOR': 'WORKING',
        'İZİNLİ': 'ON LEAVE',
        'RAPORLU': 'ON MEDICAL LEAVE',
        'GÖREVLENDİRME': 'ASSIGNED',
        '📊 Personel Türü': '📊 Personnel Type'
    }
};

// 3. Global API for other scripts
window.KDS_i18n = {
    translations: translations,
    apply: applyTranslations,
    get: function(key) {
        const lang = localStorage.getItem('kds-language') || 'tr';
        const dict = translations[lang] || translations['tr'];
        return dict[key] || key;
    },
    translateCharts: function() {
        if (typeof Plotly === 'undefined') return;
        
        document.querySelectorAll('.js-plotly-plot, .plotly-graph-div').forEach(plotEl => {
            // 1. Relayout Title
            const container = plotEl.closest('.chart-container') || plotEl.closest('.card-body');
            if (container) {
                const titleEl = container.querySelector('.chart-title') || container.querySelector('h4') || container.querySelector('h3');
                if (titleEl) {
                    // We have a better-looking HTML title, so hide the Plotly internal one
                    Plotly.relayout(plotEl, { 'title.text': '' });
                }
            }

            // 2. Restyle Axis Titles
            const layout = plotEl.layout || {};
            const updateObj = {};
            if (layout.xaxis && layout.xaxis.title && layout.xaxis.title.text) {
                updateObj['xaxis.title.text'] = this.get(layout.xaxis.title.text);
            }
            if (layout.yaxis && layout.yaxis.title && layout.yaxis.title.text) {
                updateObj['yaxis.title.text'] = this.get(layout.yaxis.title.text);
            }
            if (Object.keys(updateObj).length > 0) {
                Plotly.relayout(plotEl, updateObj);
            }

            // 3. Restyle Legends/Trace Names (Data-level leaks)
            if (plotEl.data) {
                const newNames = plotEl.data.map(trace => {
                    const key = trace.name || "";
                    return this.get(key);
                });
                Plotly.restyle(plotEl, { name: newNames });
            }
        });
    }
};

function applyTranslations(lang) {
    document.querySelectorAll('[data-t]').forEach(el => {
        const key = el.getAttribute('data-t');
        if (translations[lang] && translations[lang][key]) {
            const val = translations[lang][key];
            if (el.tagName === 'OPTION') {
                el.text = val;
            } else if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                el.placeholder = val;
            } else {
                el.innerHTML = val;
            }
        }
    });

    const loadingOverlay = document.getElementById('pageLoading');
    if (loadingOverlay) {
        const loadingText = loadingOverlay.querySelector('div:last-child');
        if (loadingText && translations[lang]) {
            loadingText.textContent = translations[lang]['Yükleniyor, lütfen bekleyin...'] || 'Loading...';
        }
    }
    
    if (window.KDS_i18n && window.KDS_i18n.translateCharts) {
        window.KDS_i18n.translateCharts();
    }
}

// 4. Initialization
document.addEventListener('DOMContentLoaded', function () {
    // Guard against accidental HTML inside <title> blocks.
    // If a template sends "<span ...>Title</span>", browser tab should still show plain text.
    if (document.title && document.title.includes('<')) {
        document.title = document.title.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
    }

    const THEME_STORAGE_KEY = 'kds-theme';
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    const themeLabel = document.getElementById('themeLabel');

    function applyPlotlyThemeToScope(theme, scope = document) {
        if (typeof Plotly === 'undefined') return;
        const isDark = theme === 'dark';
        const textColor = isDark ? '#e8f0fe' : '#0f172a';
        const mutedTextColor = isDark ? '#cbd5e1' : '#334155';
        const gridColor = isDark ? 'rgba(148, 163, 184, 0.25)' : 'rgba(100, 116, 139, 0.2)';
        const axisLineColor = isDark ? 'rgba(148, 163, 184, 0.45)' : 'rgba(71, 85, 105, 0.45)';
        const plotBgColor = isDark ? '#0b1a3a' : '#ffffff';
        const paperBgColor = isDark ? '#0b1a3a' : '#ffffff';
        const modebarBg = isDark ? 'rgba(15, 23, 42, 0.7)' : 'rgba(241, 245, 249, 0.9)';

        scope.querySelectorAll('.js-plotly-plot, .plotly-graph-div').forEach(plot => {
            if (!plot || !plot.layout) return;
            const relayoutConfig = {
                'paper_bgcolor': paperBgColor, 'plot_bgcolor': plotBgColor,
                'font.color': textColor, 'title.font.color': textColor,
                'legend.font.color': textColor, 'xaxis.color': mutedTextColor,
                'xaxis.tickfont.color': mutedTextColor, 'xaxis.title.font.color': textColor,
                'xaxis.gridcolor': gridColor, 'xaxis.zerolinecolor': gridColor,
                'xaxis.linecolor': axisLineColor, 'yaxis.color': mutedTextColor,
                'yaxis.tickfont.color': mutedTextColor, 'yaxis.title.font.color': textColor,
                'yaxis.gridcolor': gridColor, 'yaxis.zerolinecolor': gridColor,
                'yaxis.linecolor': axisLineColor,
                'coloraxis.colorbar.tickfont.color': mutedTextColor,
                'coloraxis.colorbar.title.font.color': textColor
            };
            Object.keys(plot.layout || {}).forEach(key => {
                if (/^(xaxis|yaxis)\d+$/.test(key)) {
                    relayoutConfig[`${key}.color`] = mutedTextColor;
                    relayoutConfig[`${key}.tickfont.color`] = mutedTextColor;
                    relayoutConfig[`${key}.title.font.color`] = textColor;
                    relayoutConfig[`${key}.gridcolor`] = gridColor;
                    relayoutConfig[`${key}.zerolinecolor`] = gridColor;
                    relayoutConfig[`${key}.linecolor`] = axisLineColor;
                }
            });
            try {
                Plotly.relayout(plot, relayoutConfig);
            } catch (_) {}
            const modebar = plot.parentElement?.querySelector('.modebar');
            if (modebar) modebar.style.background = modebarBg;
        });
    }

    function refreshPlotsInScope(scope = document) {
        if (typeof Plotly === 'undefined') return;
        const activeTheme = document.body.classList.contains('theme-dark') ? 'dark' : 'light';
        const isMobile = window.innerWidth <= 768;

        [80, 250, 600, 1200].forEach(delay => {
            setTimeout(() => {
                scope.querySelectorAll('.js-plotly-plot, .plotly-graph-div').forEach(plot => {
                    try {
                        var inScrollWrapper = plot.closest('.chart-scroll-wrapper');

                        if (isMobile && inScrollWrapper && plot.data) {
                            var hasBarWithManyCategories = plot.data.some(function(t) {
                                return t.type === 'bar' && t.x && t.x.length > 8;
                            });
                            if (hasBarWithManyCategories) {
                                var catCount = Math.max.apply(null, plot.data.map(function(t) {
                                    return (t.x && t.x.length) || 0;
                                }));
                                var neededWidth = Math.max(600, catCount * 45);
                                plot.style.minWidth = neededWidth + 'px';
                                Plotly.relayout(plot, { width: neededWidth, autosize: false });
                                Plotly.Plots.resize(plot);
                                return;
                            }
                        }

                        Plotly.relayout(plot, { autosize: true });
                        Plotly.Plots.resize(plot);

                        if (isMobile && plot.data) {
                            plot.data.forEach((trace, i) => {
                                if (trace.type === 'pie') {
                                    Plotly.restyle(plot, {
                                        textposition: 'inside',
                                        textinfo: 'percent',
                                        insidetextorientation: 'horizontal',
                                        automargin: true
                                    }, [i]);
                                    Plotly.relayout(plot, {
                                        'legend.font.size': 9,
                                        'legend.orientation': 'h',
                                        'legend.y': -0.3,
                                        'legend.x': 0.5,
                                        'legend.xanchor': 'center',
                                        margin: { t: 30, b: 80, l: 10, r: 10 }
                                    });
                                }
                            });
                        }
                    } catch (_) {}
                });
                applyPlotlyThemeToScope(activeTheme, scope);
            }, delay);
        });
    }

    function applyTheme(theme) {
        const normalizedTheme = theme === 'dark' ? 'dark' : 'light';
        document.body.classList.remove('theme-dark', 'theme-light');
        document.body.classList.add(`theme-${normalizedTheme}`);
        document.documentElement.setAttribute('data-theme', normalizedTheme);
        if (themeToggle) themeToggle.setAttribute('aria-pressed', normalizedTheme === 'dark' ? 'true' : 'false');
        if (themeIcon) themeIcon.textContent = normalizedTheme === 'dark' ? '☀️' : '🌙';
        if (themeLabel) themeLabel.textContent = normalizedTheme === 'dark' ? 'AYDINLIK' : 'KOYU';
        refreshPlotsInScope(document);
    }

    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY) || (document.body.classList.contains('theme-dark') ? 'dark' : 'light');
    applyTheme(savedTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const nextTheme = document.body.classList.contains('theme-dark') ? 'light' : 'dark';
            applyTheme(nextTheme);
            localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
        });
    }

    // Sidebar
    const SIDEBAR_STORAGE_KEY = 'kds-sidebar-collapsed';
    const sidebar = document.getElementById('sidebar');
    const hamburger = document.getElementById('hamburgerBtn');
    const sidebarClose = document.getElementById('sidebarClose');

    function applySidebarState(isCollapsed) {
        document.body.classList.toggle('sidebar-collapsed', isCollapsed);
        setTimeout(() => refreshPlotsInScope(document), 300);
    }
    if (window.innerWidth <= 768) {
        applySidebarState(true);
    } else {
        applySidebarState(localStorage.getItem(SIDEBAR_STORAGE_KEY) === 'true');
    }

    if (hamburger) {
        hamburger.addEventListener('click', () => {
            if (window.innerWidth <= 768 && sidebar) {
                sidebar.classList.toggle('open');
            } else {
                const isCollapsing = !document.body.classList.contains('sidebar-collapsed');
                applySidebarState(isCollapsing);
                localStorage.setItem(SIDEBAR_STORAGE_KEY, isCollapsing);
            }
        });
    }
    if (sidebarClose && sidebar) {
        sidebarClose.addEventListener('click', () => {
            sidebar.classList.remove('open');
            if (window.innerWidth > 768) { applySidebarState(false); localStorage.setItem(SIDEBAR_STORAGE_KEY, 'false'); }
        });
    }

    // Close sidebar on mobile when clicking outside
    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 768 && sidebar && sidebar.classList.contains('open')) {
            if (!sidebar.contains(e.target) && e.target !== hamburger && !hamburger.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        }
    });

    // Tabs
    document.querySelectorAll('.tabs').forEach(tabContainer => {
        const buttons = tabContainer.querySelectorAll('.tab-btn');
        const contentSelector = tabContainer.dataset.target;
        const contents = document.querySelectorAll(contentSelector + ' .tab-content');
        const storageKey = 'activeTab_' + window.location.pathname + '_' + contentSelector;
        const savedIndex = sessionStorage.getItem(storageKey);

        buttons.forEach((btn, index) => {
            btn.addEventListener('click', () => {
                buttons.forEach(b => b.classList.remove('active'));
                contents.forEach(c => c.classList.remove('active'));
                btn.classList.add('active');
                if (contents[index]) {
                    contents[index].classList.add('active');
                    sessionStorage.setItem(storageKey, index);
                    refreshPlotsInScope(contents[index]);
                }
            });
        });
        if (savedIndex !== null && buttons[savedIndex]) buttons[savedIndex].click();
    });

    window.addEventListener('resize', () => refreshPlotsInScope(document));

    // Language Switcher Initialization
    const langBtn = document.getElementById('langBtn');
    const langDropdown = document.getElementById('langDropdown');
    const langOptions = document.querySelectorAll('.lang-option');
    const currentLangFlag = document.getElementById('currentLangFlag');
    const currentLangText = document.getElementById('currentLangText');

    if (langBtn && langDropdown) {
        langBtn.addEventListener('click', (e) => { e.stopPropagation(); langDropdown.classList.toggle('active'); });
        document.addEventListener('click', (e) => { if (!langBtn.contains(e.target)) langDropdown.classList.remove('active'); });
        langOptions.forEach(option => {
            option.addEventListener('click', (e) => {
                e.preventDefault();
                const lang = option.getAttribute('data-lang');
                const flag = option.querySelector('span').textContent;
                if (currentLangFlag) currentLangFlag.textContent = flag;
                if (currentLangText) currentLangText.textContent = lang.toUpperCase();
                langOptions.forEach(opt => opt.classList.remove('active'));
                option.classList.add('active');
                localStorage.setItem('kds-language', lang);
                applyTranslations(lang);
                langDropdown.classList.remove('active');
            });
        });

        const savedLang = localStorage.getItem('kds-language') || 'tr';
        const activeOption = document.querySelector(`.lang-option[data-lang="${savedLang}"]`);
        if (activeOption) {
            const flag = activeOption.querySelector('span').textContent;
            if (currentLangFlag) currentLangFlag.textContent = flag;
            if (currentLangText) currentLangText.textContent = savedLang.toUpperCase();
            langOptions.forEach(opt => opt.classList.remove('active'));
            activeOption.classList.add('active');
            applyTranslations(savedLang);
        }
    }

    // Page Loading Overlay
    const pageLoading = document.getElementById('pageLoading');
    window.addEventListener('beforeunload', () => { if (pageLoading) pageLoading.classList.add('active'); });
    document.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', function() {
            const href = this.getAttribute('href');
            const target = this.getAttribute('target');
            if (href && !href.startsWith('#') && !href.startsWith('javascript:') && (!target || target === '_self')) {
                if (!this.hasAttribute('download')) if (pageLoading) pageLoading.classList.add('active');
            }
        });
    });
    window.addEventListener('pageshow', (event) => { if (event.persisted && pageLoading) pageLoading.classList.remove('active'); });

    console.log('🏥 KDS Panel hazir.');
});
