# io-Guard: Otonom Hesaplama Aracısı

**io-Guard**, karmaşık makine öğrenimi iş akışlarını optimize etmek için devasa dağıtık hesaplama ağlarına (örneğin **io.net**) entegre olan akıllı bir sistemdir. Kümeleme, donanım seçimi ve güvenli bağlantı süreçlerini soyutlayan **Ajan Tabanlı Katman-2 (Agentic Layer-2)** çözümüdür.

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Status](https://img.shields.io/badge/status-Alpha%20v1.1-orange.svg) ![Docker](https://img.shields.io/badge/docker-ready-blue)

---

## 🚀 Temel Özellikler

Sistem, DePIN (Merkeziyetsiz Fiziksel Altyapı) ağlarında **gerçek** işlemler yapabilme yeteneğine sahiptir:

1.  **Omurga (The Backbone):** Supabase destekli veritabanı ile tüm sohbetler, iş geçmişi ve piyasa verileri kalıcı olarak saklanır.
2.  **Gerçek Gözler (Real Eyes):** `api.io.solutions` entegrasyonu ile **canlı GPU piyasasını** (Fiyat, Stok, Kiralama Durumu) anlık takip eder.
3.  **Güvenli El (Secure Hand):** SSH anahtarlarınızı şifreli saklar ve kiraladığınız sunuculara `Paramiko` kütüphanesi ile güvenli tünel açar.
4.  **Akıllı Ajanlar:** DeepSeek-V3 destekli ajanlar kodunuzu analiz eder ve en uygun donanımı önerir.

## 🧠 Çekirdek Ajanlar (Backend)

| Ajan | Rol | İşlev |
| :--- | :--- | :--- |
| **🕵️ Auditor** | Statik Analiz | Kodunuzu okur, kütüphane ve VRAM gereksinimlerini belirler. |
| **🎯 Sniper** | Piyasa Arbitrajı | Canlı API verisiyle `Skor = (Fiyat/Performans) + Güvenilirlik` analizi yapar. |
| **🔐 Connector** | Güvenli Bağlantı | SSH Tünelleme ve sunucu sağlığı (uptime) kontrolü sağlar. |
| **🤖 Assistant** | Genel Zeka | Teknik destek veren, veritabanı hafızalı sohbet botu. |

## 💻 Arayüz (Frontend)

**Next.js 14**, **Tailwind CSS** ve **Shadcn/UI** ile geliştirilmiş modern bir konsol:

-   **Dashboard:** Canlı piyasa verileri (Fiyatlar, Doluluk Oranları) ve sistem sağlığı.
-   **Analyze:** Kodunuzu yapıştırın, Ajanlar analiz etsin.
-   **Deploy:** İster simülasyon yapın, ister **SSH Anahtarı** ekleyerek gerçek sunucunuza bağlanın.
-   **Chat:** Asistan ile konuşun, geçmiş konuşmalarınızı kaybetmeyin.

---

## ⚡ Kurulum ve Çalıştırma

### Gereksinimler
-   [Docker Desktop](https://www.docker.com/products/docker-desktop/)
-   Git
-   Supabase Hesabı (Veritabanı için)

### Adım Adım Kurulum

1.  **Depoyu Klonlayın**
    ```bash
    git clone https://github.com/aliozen0/sentinel-io.git
    cd io-guard
    ```

2.  **Ortam Değişkenleri**
    `.env.example` dosyasını `.env` olarak kopyalayın ve Supabase bilgilerinizi girin:
    ```bash
    cp .env.example .env
    # .env dosyasını açıp SUPABASE_URL ve SUPABASE_KEY alanlarını doldurun.
    ```

3.  **Sistemi Başlatın**
    Tüm servisleri (Backend & Frontend) ayağa kaldırın:
    ```bash
    docker-compose up --build
    ```

4.  **Veritabanı Kurulumu**
    Supabase SQL Editöründe `backend/db/schema.sql` dosyasındaki tabloları oluşturun (`chat_messages`, `jobs`, `ssh_keys`).

5.  **Erişim**
    -   **Frontend:** [http://localhost:3000](http://localhost:3000)
    -   **Backend API:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📂 Proje Yapısı

```
io-guard/
├── backend/                # Python FastAPI (Beyin)
│   ├── agents/             # Ajanlar (Sniper, Auditor)
│   ├── db/                 # Veritabanı İstemcisi & Şema
│   ├── services/           # Servisler (SSH Manager)
│   └── main.py             # API Endpoint'leri
├── frontend/               # Next.js 14 (Arayüz)
│   ├── app/                # Sayfalar (Dashboard, Deploy)
│   └── components/         # UI Bileşenleri (SSH Modal, Charts)
└── docker-compose.yml      # Orkestrasyon
```

## 🔮 Yol Haritası (Roadmap)

-   [x] **Adım 1: Veri Omurgası** (Supabase Entegrasyonu) ✅
-   [x] **Adım 2: Gerçek Piyasa** (Canlı API Verisi) ✅
-   [x] **Adım 3: Güvenli Bağlantı** (SSH & Paramiko) ✅
-   [ ] **Adım 4: Dosya Transferi** (Lokal Yükleme & Wget) 🚧
-   [ ] **Adım 5: Canlı Yürütme** (Remote Docker Execution)

---

## 📄 Lisans

Bu proje MIT Lisansı altında lisanslanmıştır.
