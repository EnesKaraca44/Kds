# KDS Servis Kurulumu

KDS bir web uygulamasıdır ve varsayılan olarak 8032 portunda çalışır. Tüm yapılandırma ayarlar.py dosyasında toplanmıştır. Python paket listesi için KUTUPHANELER.md dosyasına bakın.

## İlk kurulum

Sunucuda flask_app klasörüne geçin. Sanal ortam oluşturup bağımlılıkları yükleyin ve ayar dosyasını hazırlayın.
 
Gerekli Python paketlerini KUTUPHANELER.md dosyasına göre pip ile kurun.

ayarlar.py içinde veritabanı bağlantı bilgilerini DATABASE bölümünde güncelleyin. Aynı ağdaki bilgisayarlardan erişim için SERVER.public_host alanına sunucunun gerçek IP adresini yazın. Rapor API anahtarı projede sabittir, ayrıca tanımlamanız gerekmez.

Kurulumu doğrulamak için debug_start.bat dosyasını çalıştırabilir veya venv\Scripts\python.exe app.py komutu ile uygulamayı başlatabilirsiniz. Tarayıcıdan localhost adresini açarak giriş sayfasını görmelisiniz.

## Windows servisi

Kalıcı çalışma için uygulama Windows servisi olarak kurulur. Debug veya manuel çalışan sunucuyu kapatın; aynı port iki süreç tarafından kullanılamaz.

servis_kur.bat dosyasına sağ tıklayıp Yönetici olarak çalıştırın. Alternatif olarak Yönetici CMD penceresinde venv\Scripts\python.exe install_service.py komutunu kullanabilirsiniz. Kurulan servisin adı KDSFlaskService dir.

## Erişim adresleri

Sunucunun kendisinden erişim http://localhost:8032 adresi ile yapılır. Dinleme adresi 0.0.0.0 olduğunda aynı yerel ağdaki diğer bilgisayarlar sunucunun IP adresi ve 8032 portu ile bağlanabilir. Örnek: http://192.168.1.100:8032

Ağdan erişim sağlanamıyorsa Windows güvenlik duvarında 8032 numaralı TCP portuna izin vermeniz gerekir. Aşağıdaki komutu Yönetici CMD ile çalıştırın.

```cmd
netsh advfirewall firewall add rule name="KDS Flask 8032" dir=in action=allow protocol=TCP localport=8032
```

## Servis yönetimi

Servisin durumunu sc query KDSFlaskService komutu ile kontrol edebilirsiniz. net start KDSFlaskService ile başlatır, net stop KDSFlaskService ile durdurursunuz. Hata ayıklama için service-stderr.log dosyasının içeriğine bakın.

## Sık karşılaşılan durumlar

Port zaten kullanılıyorsa debug veya run_server sürecini kapatın. Menülerde veri görünmüyorsa 8053 portundaki Rapor API servisinin çalıştığını doğrulayın. Giriş sayfası tekrar tekrar açılıyorsa veritabanında kullanıcının KULLANICI_KDS alanının 1 olduğunu kontrol edin. Ağdan sayfa açılmıyorsa güvenlik duvarı kuralını ve public_host IP değerini gözden geçirin.
