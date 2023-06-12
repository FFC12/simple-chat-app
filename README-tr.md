## Basit Sohbet Uygulaması

Bu proje, Python 3.11 kullanılarak geliştirilmiş basit bir sohbet uygulamasıdır. FastAPI, MongoDB, Redis ve Socket.io ile oluşturulmuştur. Kullanıcılar uygulamaya kayıt olabilir ve giriş yapabilir, böylece kullanıcı dostu arayüz üzerinden birbirleriyle özel mesajlaşabilirler. Çevrimiçi kullanıcılar gerçek zamanlı olarak görüntülenir. Arka plandaki akış Docker ve docker-compose kullanılarak yönetilir. Uygulama Heroku üzerinde yayınlanmıştır.
#### Temel Özellikler:

* Kullanıcı kaydı ve giriş işlevselliği
* Kullanıcı kimlik doğrulama için JWT (JSON Web Token) kullanımı
* Kullanıcı hesaplarının güvenli şifrelemesi
* Sohbet geçmişi için kullanıcı sohbet verilerinin MongoDB'de depolanması
* Verimli kullanıcı oturum yönetimi için Redis kullanımı
* Geliştirilmiş güvenlik için otomatik oturum süresi sona erme
* Kullanıcı oturum kapatma özelliği
* Oturum süresinin uzatılması için kullanıcı oturum yenileme
* Kullanıcılar arasında özel mesajlaşma yeteneği
* Gerçek zamanlı mesaj gönderme ve alma
* Gerçek zamanlı resim gönderme ve alma
* Gerçek zamanlı emoji gönderme ve alma
* Gerçek zamanlı video gönderme ve alma (yapılacak)
* Gerçek zamanlı dosya gönderme ve alma (yapılacak)
* Sohbet uygulamasında çevrimiçi kullanıcıların görüntülenmesi
* Kullanıcı deneyimini geliştirmek için okunmamış mesaj göstergesi
* Kullanıcılar arasında en son alınan mesajın görüntülenmesi
* En son mesajın zaman damgasının görüntülenmesi

Test etmek için:
https://simple-chat-app-fastapi.herokuapp.com/
