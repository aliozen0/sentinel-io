# �️ io-Guard: Agentic FinOps Orchestrator (v2.1)

> **"Bir sistemi izlemek yetmez; onu finansal olarak yönetmek gerekir."**

**io-Guard**, io.net ekosistemi için geliştirilmiş, otonom bir **FinOps ve Kaynak Yönetim Ekibidir**. Sıradan bir monitoring aracı değildir; yapay zeka ajanlarından oluşan bir "takım" gibi çalışır. Sorunları tespit eder, kök nedeni bulur, **para kaybını ($) hesaplar** ve otonom olarak aksiyon alır.

![Agentic Workflow](https://via.placeholder.com/1200x400.png?text=Watchdog+->+Diagnostician+->+Accountant+->+Enforcer)

---

## 🧠 Nasıl Çalışır? (The Agentic Team)

Sistem, **SOLID** prensiplerine göre tasarlanmış, "Chain of Responsibility" (Sorumluluk Zinciri) mimarisini kullanan 4 uzman ajandan oluşur:

| Simge | Ajan | Rol | Görev |
| :--- | :--- | :--- | :--- |
| 👁️ | **Watchdog** | Gözcü | Binlerce veri noktasını tarar, anomaliyi (Latency > 0.5s, Temp > 80C) yakalar. |
| 🩺 | **Diagnostician** | Doktor | Sorunun nedenini teşhis eder (Örn: *Thermal Throttling*, *Network Packet Loss*). |
| 💸 | **Accountant** | Muhasebeci | Teknik hatayı paraya çevirir. *"Bu yavaşlık size saatte 2.50$ kaybettiriyor"* der. |
| 🛡️ | **Enforcer** | İnfazcı | Kayıp eşik değerini (0.50$/saat) geçerse düğümü (Worker) otonom olarak kapatır. |

---

## 🚀 Özellikler

*   **Otonom Karar Mekanizması:** İnsan müdahalesine gerek kalmadan "Tespit Et -> Hesapla -> Çöz" döngüsünü çalıştırır.
*   **FinOps Odaklı (ROI):** Sadece teknik metrikleri değil, finansal etkiyi raporlar.
*   **Chaos Testing Mode:** Sistemin dayanıklılığını test etmek için yapay sorunlar (Chaos) enjekte edilebilir.
*   **Premium Mission Control:** Streamlit tabanlı, logları ve canlı finansal tasarrufu gösteren modern arayüz.

---

## �️ Kurulum ve Çalıştırma

### Gereksinimler
*   Docker & Docker Compose
*   io.net Intelligence API Key (`IO_API_KEY`)

### Hızlı Başlangıç

1.  **Repo'yu Klonlayın ve Hazırlayın:**
    ```bash
    git clone https://github.com/your-username/io-guard.git
    cd io-guard
    cp .env.example .env
    ```

2.  **API Anahtarını Girin:**
    `.env` dosyasını açın ve `IO_API_KEY`'inizi yapıştırın.

3.  **Sistemi Başlatın:**
    ```bash
    docker compose up --build -d
    ```

4.  **Mission Control'e Bağlanın:**
    Tarayıcınızda [http://localhost:8501](http://localhost:8501) adresine gidin.

---

## 🔥 Chaos Mode (Şov Zamanı)

Sistemin gerçek gücünü görmek için "sorunsuz" bir sistem izlemek yetmez. Sisteme kaos enjekte edin:

1.  `docker-compose.yml` dosyasını açın.
2.  `worker-3` servisi altındaki `CHAOS_MODE=False` değerini `True` yapın.
3.  Değişikliği uygulayın: `docker compose up -d`.
4.  Arayüzde **"RUN AGENTIC DIAGNOSTICS"** butonuna basın ve ajanların tepkisini izleyin!

---

## � Proje Yapısı

```plaintext
io-guard/
├── io-Guard-Autonomous-FinOps.yaml # io.net Workflow Blueprint (v2.1)
├── backend/
│   ├── agents/                     # AI Ajanları (Watchdog, Enforcer vs.)
│   ├── services/                   # Orchestrator (Yönetici Servis)
│   ├── main.py                     # API Gateway
│   └── logger.py                   # Merkezi Log Sistemi
├── frontend/                       # Streamlit Dashboard (Mission Control)
├── workers/                        # GPU Simülasyonu
└── docker-compose.yml              # Altyapı
```

---

## 🌟 Hackathon Uyumluluğu

Bu proje **io.net Hackathon** katılım şartlarına tam uyumludur:
- [x] **Agentic Workflow:** io.net Intelligence API ile çalışan çoklu ajan sistemi.
- [x] **New Architecture:** Monolitik değil, mikroservis ve SOLID mimari.
- [x] **FinOps & Utility:** Gerçek dünya problemi (GPU kaynak israfı) çözer.

---

*Powered by io.net Intelligence API & OpenAI LLMs*
