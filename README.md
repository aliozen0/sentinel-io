# io-Guard: Otonom Hesaplama Aracısı

**io-Guard**, karmaşık makine öğrenimi iş akışlarını optimize etmek için devasa dağıtık hesaplama ağlarına (örneğin **io.net**) basit sorular soran bir sistemdir. Kümeleme (clustering), donanım seçimi ve ortam yapılandırmasının karmaşıklığını soyutlayan **Ajan Tabanlı Katman-2 (Agentic Layer-2)** çözümüdür.

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Status](https://img.shields.io/badge/status-MVP%20v1.0-green.svg) ![Docker](https://img.shields.io/badge/docker-ready-blue)

---

## 🚀 Vizyon

Merkeziyetsiz Fiziksel Altyapı Ağları (DePIN) çağında, hesaplama gücü boldur ancak parçalıdır. **io-Guard**, aşağıdaki işlemleri gerçekleştiren yapay zeka ajanlarını kullanarak sizin akıllı aracınız (broker) olarak hizmet eder:
1.  **Denetle (Audit):** Kodunuzu kaynak gereksinimleri için analiz eder.
2.  **Avla (Snipe):** En iyi GPU fırsatlarını yakalamak için piyasayı tarar.
3.  **Tasarla (Architect):** Mükemmel Docker ortamını kurgular.
4.  **Yürüt (Execute):** Eğitim sürecini otonom olarak başlatır ve izler.

## 🧠 Çekirdek Ajanlar (Backend)

Sistem, **DeepSeek-V3** (via `io Intelligence`) tarafından desteklenen Mikro-Ajan Mimarisi ile çalışır:

| Ajan | Rol | İşlev |
| :--- | :--- | :--- |
| **🕵️ The Auditor (Denetçi)** | Statik Analiz | Python kodunu ayrıştırarak VRAM (GB) ve kütüphane gereksinimlerini (PyTorch/TF) tahmin eder. |
| **🎯 The Sniper (Keskin Nişancı)** | Piyasa Arbitrajı | `Skor = (Fiyat/Performans) + Güvenilirlik` formülüyle en iyi düğümleri (node) bulur. |
| **🏗️ The Architect (Mimar)** | Ortam Yöneticisi | Kod gereksinimlerini deterministik olarak optimize edilmiş Docker imajlarıyla eşleştirir (örn. `ray-project/ray-ml`). |
| **🤖 The Assistant (Asistan)** | Mantık Çekirdeği | Teknik destek ve rehberlik için arayüze entegre edilmiş genel amaçlı bir yapay zeka sohbet botu. |

## 💻 Arayüz (Frontend)

**Next.js 14**, **Tailwind CSS** ve **Shadcn/UI** ile geliştirilmiştir.

-   **Dashboard:** Sistem sağlığı ve piyasa fırsatlarının gerçek zamanlı özeti.
-   **Analyze (Analiz):** Anında Denetim Raporu ve Dağıtım Planı almak için eğitim kodunuzu yapıştırın.
-   **Chat:** **DeepSeek-V3** destekli asistan ile etkileşime geçin.
-   **Deploy (Dağıtım):** Gerçek kredileri harcamadan önce dağıtım günlüklerini önizlemek için "Simülasyon Konsolu".

## 🛠️ Teknoloji Yığını

-   **Frontend:** Next.js 14 (App Router), React 18, Tailwind CSS v3, Shadcn/UI.
-   **Backend:** Python 3.9, FastAPI, Uvicorn.
-   **Yapay Zeka Modeli:** DeepSeek-V3 (`.env` üzerinden ayarlanabilir).
-   **Altyapı:** Docker & Docker Compose (Çoklu konteyner orkestrasyonu).

---

## ⚡ Başlarken

### Gereksinimler
-   [Docker Desktop](https://www.docker.com/products/docker-desktop/)'ın kurulu ve çalışıyor olması.
-   Git.

### Kurulum

1.  **Depoyu Klonlayın**
    ```bash
    git clone https://github.com/aliozen0/sentinel-io.git
    cd io-guard
    ```

2.  **Ortam Kurulumu**
    Örnek ortam dosyasını kopyalayın ve anahtarlarınızı yapılandırın.
    ```bash
    cp .env.example .env
    ```
    *`.env` dosyasını düzenleyerek varsa `IO_API_KEY` ekleyebilir veya `IO_MODEL_NAME` değiştirebilirsiniz.*

3.  **Sistemi Başlatın**
    ```bash
    docker-compose up --build
    ```

4.  **Uygulamaya Erişin**
    -   **Frontend (Arayüz):** [http://localhost:3000](http://localhost:3000)
    -   **Backend API Dokümanı:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📂 Proje Yapısı

```
io-guard/
├── backend/                # FastAPI Servisi (Beyin)
│   ├── agents/             # Ajan Uygulamaları (Auditor, Sniper vb.)
│   ├── db/                 # Veritabanı Şeması
│   └── main.py             # API Giriş Noktası
├── frontend/               # Next.js Uygulaması (Yüz)
│   ├── app/                # App Router Sayfaları
│   ├── components/         # Yeniden Kullanılabilir UI Bileşenleri
│   └── Dockerfile          # Node.js 20 Konteyneri
├── frontend_old/           # Arşivlenmiş Eski Frontend (Yoksayıldı)
├── docker-compose.yml      # Orkestrasyon Yapılandırması
└── .env                    # Sırlar ve Ayarlar
```

## 🔮 Yol Haritası

-   [x] **Faz 1: MVP Çekirdek** (Ajanlar, Simülasyon, UI)
-   [ ] **Faz 2: Canlı Entegrasyon** (SSH Tünelleme, Gerçek Market API)
-   [ ] **Faz 3: Otonom Mod** (Kendi kendine iyileşme, Otomatik ölçeklendirme)
-   [ ] **Faz 4: Gelir Modeli** (Kullanıcı Kredi Sistemi)

---

## 📄 Lisans

Bu proje MIT Lisansı altında lisanslanmıştır.
