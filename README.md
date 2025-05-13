# Minecraft-Server-Manager
Minecraft sunucunuzu kolayca başlatın, yönetin, mod kurun, yedek alın ve çok daha fazlasını yapın!

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Tkinter](https://img.shields.io/badge/Arayüz-Tkinter-green)
![Lisans](https://img.shields.io/badge/Lisans-MIT-yellow)
![Durum](https://img.shields.io/badge/Durum-Aktif-brightgreen)

## 🚀 Özellikler

- ✅ Sunucu Başlatma/Durdurma/Yeniden Başlatma
- 🔧 Minecraft ve modpack kurulumu (CurseForge & Vanilla)
- ☕ Gerekli Java sürümünü otomatik indirip kurma
- 💾 Sunucu yedekleme ve geri yükleme
- 📂 Dosya düzenleme (config dosyaları vs.)
- 🌐 Entegre FTP sunucu (kullanıcı adı/parola ve port ayarlanabilir)
- 🔌 RCON şifre ve port ayarı + Konsol logları
- 🛢️ Portable MySQL kurulumu ve veritabanı yönetimi
- 🖥️ Log görüntüleme alanı
- 🖱️ Tamamen grafik arayüz (Tkinter)

## 🛠 Kurulum

> Python 3.8+ kurulu olmalıdır.

1. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```
2. Programı Çalıştırma
```bash
python main.py
```
## Özellikler

- **Sunucu Kurulumu**:
  - Vanilya Minecraft sunucularını (1.16.5 - 1.21 sürümleri) otomatik Java sürümü seçimiyle kurun.
  - SkyFactory 4 gibi CurseForge mod paketlerini mod indirme ve sunucu kurulumuyla birlikte kurun.
- **Mod Yönetimi**:
  - CurseForge API'sini kullanarak mod paketleri için modları otomatik indirir.
  - Mod indirme ilerlemesini gerçek zamanlı gösterir (ör. "Modlar İndiriliyor .... Toplam: 100 İndirilen: 5").
- **Sunucu Yönetimi**:
  - Tek tıkla sunucuyu başlatma, durdurma ve yeniden başlatma.
  - Sunucu durumunu, çevrimiçi oyuncuları ve IP/port bilgilerini gerçek zamanlı izleme.
  - Sunucu özelliklerini (port, maksimum oyuncu, MOTD vb.) arayüz üzerinden yapılandırma.
- **Yedekleme ve Geri Yükleme**:
  - Yeni sunucu veya mod paketi kurmadan önce yedek alma.
  - Kurulum hatalarında önceki sunucu durumunu geri yükleme.
- **Java Desteği**:
  - Gerekli Java sürümünü (ör. SkyFactory 4 için Java 17, yeni sürümler için Java 21) otomatik indirir ve yapılandırır.
  - Java sürüm uyumsuzluklarını algılar ve uygun sürümü kurar.
- **Kullanıcı Dostu Arayüz**:
  - Tkinter tabanlı, temiz bir arayüzle mod paketlerini tarama, logları görüntüleme ve sunucuları yönetme.
  - Renk kodlu (BİLGİ, UYARI, HATA) gerçek zamanlı konsol çıktıları.
- **Çapraz Platform**:
  - Windows ve Linux desteği (macOS test edilmemiştir).

## Ekran Görüntüleri


## Ön Koşullar

- **Python**: 3.8 veya üzeri sürüm.
- **İşletim Sistemi**: Windows veya Linux (macOS desteklenmeyebilir, test edilmemiştir).
- **Bağımlılıklar**: Gerekli Python paketlerini kurun (bkz. [Kurulum](#kurulum)).
- **CurseForge API Anahtarı**: Mod paketleri ve modları indirmek için gereklidir (bkz. [Yapılandırma](#yapılandırma)).
- **İnternet Bağlantısı**: Java, Minecraft sunucuları ve mod paketlerini indirmek için gerekli.


### İndirme Yöntemi
GitHub'da dosya yükleme ve paylaşma işlemi için doğrudan bir indirme bağlantısı oluşturmak yerine, aşağıdaki adımları izleyerek `README.md` dosyasını yerel olarak oluşturabilir ve GitHub'a yükleyebilirsiniz. Ancak, dosyayı kolayca indirmeniz için bir metin dosyası olarak hazırlayıp paylaşmak istersem, GitHub Gist veya benzeri bir hizmet kullanabilirim. Şimdilik, yukarıdaki içeriği kopyalayıp kullanmanız için adımları aşağıda açıklıyorum:

1. **Yerel Olarak Oluşturma**:
   - Bir metin editörü (ör. Notepad++, VS Code) açın.
   - Yukarıdaki `README.md` içeriğini kopyalayıp yapıştırın.
   - Dosyayı proje kök dizininde `README.md` olarak kaydedin (UTF-8 kodlamasıyla).

2. **GitHub'a Yükleme**:
   - Projenizi GitHub'da bir depoya yüklemek için:
     ```bash
     git add README.md
     git commit -m "README dosyası eklendi"
     git push origin main
     ```
   - Deponuz yoksa, yeni bir depo oluşturun:
     ```bash
     git init
     git remote add origin https://github.com/<kullanıcı-adınız>/minecraft-server-manager.git
     git add .
     git commit -m "İlk commit: Minecraft Server Manager"
     git push -u origin main
     ```

3. **Doğrudan İndirme (Alternatif)**:
   - Yukarıdaki içeriği bir `README.md` dosyası olarak yerel bilgisayarınıza kaydetmek için:
     - İçeriği kopyalayın.
     - Yeni bir dosya oluşturun (`README.md`).
     - İçeriği yapıştırın ve kaydedin.
   - İsterseniz, içeriği bir Gist'e yükleyip indirme bağlantısı sağlayabilirim. Bunu yapmamı isterseniz, lütfen belirtin!

Eğer içeriği bir Gist veya başka bir platform üzerinden indirme bağlantısı olarak paylaşmamı isterseniz, lütfen belirtin. Ayrıca, README'de ek değişiklikler, GitHub kurulumu veya başka özellikler (ör. iş parçacığı kullanımı) için destek isterseniz, hemen yardımcı olabilirim! 😊 Projenizi GitHub'da yayınlama konusunda başarılar!
