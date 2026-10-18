# 🌸 Seher'in AUZEF Çalışma Asistanı

Telefon ve bilgisayardan kullanılabilen, **7 dersin çalışma PDF'lerini** ve **1.511 açıklamalı test sorusunu** bir araya getiren özel Streamlit uygulaması.

## Özellikler
- 7 ders: Anatomi, Bilimsel Araştırma Teknikleri, Sosyolojiye Giriş, Psikoloji, Yabancı Dil I, Türk Dili I, Atatürk İlkeleri ve İnkılap Tarihi I.
- Her dersin birleşik PDF çalışma rehberini uygulama içinde sayfa sayfa okuma ve indirme.
- Ders bazında ünite seçimi, karma testler ve soru sayısı seçimi.
- **Testi bitir** sonrası doğru, yanlış, boş ve başarı yüzdesi.
- Doğru ve yanlış yapılan **tüm soruların seçeneklerini ve açıklamalarını** inceleme.
- Sonuç geçmişi; CSV olarak indirme.
- Şifreyle giriş. Mobil uyumlu arayüz.

> Sorular daha önce kullanıcı için hazırlanan çalışma rehberlerinden aktarılmıştır; üniversitenin resmî çıkmış soruları değildir. PDF'ler ve soru bankası **uygulama_paketi.zip** içinde, kaynak kod ve verilerle birlikte bulunur.

## Streamlit Community Cloud üzerinde yayınlama
1. [share.streamlit.io](https://share.streamlit.io/) adresine GitHub hesabınla giriş yap.
2. **Create app → Deploy a public app from GitHub** (menü metni değişebilir) bölümünde bu **özel** depoyu seç.
3. **Branch:** `main`; **Main file path:** `app.py`.
4. App settings → **Secrets** alanına kendi belirlediğin güçlü şifreyi şöyle ekle:
   ```toml
   APP_PASSWORD = "buraya-guclu-kisisel-sifre"
   ```
5. Deploy'e bas. Açılan uygulama bağlantısını Seher'in telefonunda tarayıcıya kaydedebilirsin. **Özel GitHub deposu, yayınlanan uygulamanın kendiliğinden özel olduğu anlamına gelmez**; bu nedenle uygulama şifresini kesinlikle GitHub'a yazma veya herkese paylaşma.

## Yerel çalıştırma
Python 3.11+:
```bash
pip install -r requirements.txt
# Uygulama APP_PASSWORD ortam değişkenini ya da .streamlit/secrets.toml dosyasını okur.
streamlit run app.py
```

## Teknik bilgiler
- **app.py** kök giriş dosyası, **uygulama_paketi.zip** içindeki doğrulanmış kaynak kodunu ve ders içeriklerini yerel çalışma klasörüne çıkarıp çalıştırır.
- Gereken paketler: Streamlit, PyMuPDF.
- Test geçmişi çalışılan sunucunun SQLite dosyasındadır. Streamlit Community Cloud'da yeniden başlatma/yeniden dağıtım sonrasında geçmiş silinebilir. Önemli sonuçlarını CSV olarak indirip sakla.
- Kaynak kitapları değil, hazırlanmış çalışma PDF'leri kullanılmıştır. Gizli bilgi veya şifre depoya eklenmemelidir.

Geliştirme amacı: Seher'in derslerini düzenli ve anlaşılır biçimde çalışabilmesi. ❤️
