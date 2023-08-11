# Resim İşaretleme Arayüzü

Bu proje, resimleri işaretleme ve verileri saklama amacıyla kullanılan basit bir PyQt5 tabanlı bir arayüzü içerir. Kullanıcılar resimleri "Evet" veya "Hayır" olarak işaretleyebilir, işaretlenen veriler bir SQLite veritabanına kaydedilir ve kullanıcıların girdiği isim, grup ID ve işaretleme durumu saklanır.

## Gereksinimler

- Python 3.x
- PyQt5
- SQLite3

Gerekli kütüphaneleri yüklemek için aşağıdaki komutları kullanabilirsiniz:

```
pip install PyQt5
```

## Kullanım

- İsim, soyisim girmeniz gereken bir alan bulunmaktadır.
- "ACİL", "RADYOLOJİ", "PEDİATRİ", "KBB" gibi grup ID'leri arasından seçim yapabilirsiniz.
- "Evet" veya "Hayır" düğmelerine tıklayarak resimleri işaretleyebilirsiniz.
- İşaretlediğiniz resimler ve veriler SQLite veritabanına kaydedilir.
- İşaretleme yapmadan önce resmi seçtiğinizde, resim önizlemesi görüntülenir.

## Lisans

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır.