# 🛡️ io-Guard: Agentic FinOps Orchestrator (v3.2)

> **"Gerçekçilik, Simülasyonda Değil, Fizik Kurallarındadır."**

**io-Guard v3.2**, io.net ekosistemi için tasarlanmış, **Termodinamik Fizik Motoru (DeepSim)** üzerine kurulu, ultra-gerçekçi bir **Otonom FinOps ve Kaynak Yönetim Ekibidir**.

Bu sürümde ("Hollywood Update"), Worker node'lar basit scriptler olmaktan çıkıp, fan devrinden termal macun sağlığına kadar simüle edilen **Dijital İkizlere (Digital Twins)** dönüşmüştür.

---

## 🌪️ DeepSim Physics Engine & Digital Twins

Sistem artık sadece "Latency arttı" demez. Bir Worker'ın **neden** yavaşladığını fiziksel kanıtlarla bilir:

| Bileşen | Simülasyon Özelliği | Etki |
| :--- | :--- | :--- |
| **Cooling** | ❄️ Thermodynamic Loop | Fan RPM, Isı (Temp), Soğutma Kapasitesi (Cooling Capacity). |
| **Network** | 🌐 Integrity Check | Paket Kaybı, Jitter, Port Sağlığı. |
| **Power** | ⚡ Efficiency | Güç kaçağı, Voltage droop ve ısıya etkisi. |
| **Logic** | 🧠 Throttling | `Temp > 95°C` olduğunda sistem **Termal Throttling** uygular ve Clock Hızını düşürür. |

---

## � The Physics-Aware Agent Swarm

Ajanlar artık sadece log okumaz; **Fizik Kurallarını Denetler**. Loglarda bir anormallik gördüklerinde "Neden?" sorusunu sorarlar.

| Simge | Ajan | Yeni Süper Gücü |
| :--- | :--- | :--- |
| 👁️ | **Watchdog** | **Physics Violation Detector**: "Fan %100 dönüyor ama ısı düşmüyor. Bu fizik kurallarına aykırı!" |
| 🩺 | **Diagnostician** | **Root Cause Analysis**: "Aktif Soğutma Arızası (Active Cooling Failure) veya Termal Macun Kuruması (Thermal Paste Degraded)." |
| 💸 | **Accountant** | **Thermal Waste Calc**: "Throttling yüzünden donanımın %40'ı ısıya gidiyor. Saatlik zarar: $6.40." |
| 🛡️ | **Enforcer** | **Async Repair**: Sadece kapatmaz. Önce "Teknisyen" (API çağrısı) yollayıp parça değişimi dener. |

---

## 🔮 Agentic VRAM Oracle (Pre-Flight Check)

IO.net ekosisteminde en çok karşılaşılan "Out of Memory (OOM)" hatalarını önlemek için geliştirdiğimiz **3 Aşamalı Kod Denetim Hattı**:

1.  **🧩 Code Parser Agent**: Yüklenen Python eğitim kodunu (`train.py`) analiz eder. Model mimarisini (Llama-3, ResNet), batch size'ı ve optimizer'ı ayıklar.
2.  **🧮 VRAM Calculator**: Donanım mühendisi gibi çalışır. Parametre sayısı ve veri tiplerine (fp16, bf16) göre gereken VRAM miktarını **GB cinsinden hesaplar**.
3.  **💡 Optimization Advisor**: Mevcut donanım (örn. RTX 4090 24GB) yetersizse, *Gradient Accumulation*, *LoRA* veya *CPU Offloading* gibi teknik tavsiyeler verir.

> **Sonuç:** "Deploy" butonuna basmadan önce kodunuzun çalışıp çalışmayacağını %99 doğrulukla bilirsiniz.

---

## � DeepSim Lab: Engineering Cockpit

Yeni arayüzümüz, bir **Mühendislik Kokpiti** seviyesine çıkarıldı.

*   **Real-Time Telemetry**: Isı, Fan Hızı, Clock Hızı anlık takip.
*   **Health Bars**:
    *   ❄️ **Fan Integrity**: Fan kabloları ve motor sağlığı.
    *   🌐 **Link Quality**: Network portu fiziksel durumu.
*   **Sabotage Tools (Mission Control):**
    *   ✂️ **Cut Fan Wire**: Fanı fiziksel olarak devre dışı bırak. (Sonuç: Isı patlaması).
    *   🔨 **Damage Port**: Network kablosunu zedele.

---

## 🛠️ Kurulum ve Çalıştırma

### Gereksinimler
*   Docker & Docker Compose
*   io.net Intelligence API Key (`IO_API_KEY`)

### Hızlı Başlangıç

1.  **Repo'yu Klonlayın:**
    ```bash
    git clone https://github.com/aliozen0/sentinel-io.git
    cd sentinel-io 
    cp .env.example .env
    ```

2.  **API Anahtarını Girin:**
    `.env` dosyasını açın ve `IO_API_KEY`'inizi yapıştırın.

3.  **Sistemi Başlatın:**
    ```bash
    docker compose up --build -d
    ```

4.  **DeepSim Lab'e Bağlanın:**
    Tarayıcınızda [http://localhost:8501](http://localhost:8501) adresine gidin.

### 🎮 Nasıl Oynanır? (Demo Senaryosu)

1.  Arayüzden **"🛡️ ACTIVE WATCHDOG (Auto-Pilot)"** anahtarını açın.
2.  Sol menüdeki **"✂️ Cut Fan Wire"** butonuna basarak bir Worker'ı sabote edin.
3.  **Filmi İzleyin 🍿:**
    *   Isı 90°C'yi geçecek.
    *   **KERNEL ALERT** devreye girecek.
    *   Ajanlar uyanacak, sorunu teşhis edecek (`Active Cooling Failure`).
    *   Enforcer, teknisyen yollayıp fanı tamir edecek.
    *   Isı tekrar normale dönecek.

---

## 📂 Proje Yapısı

```plaintext
io-guard/
├── backend/
│   ├── agents/                     # Physics-Aware AI Ajanları
│   ├── services/orchestrator.py    # Async Agent Orchestrator
│   ├── main.py                     # Kernel & Chaos API
│   └── requirements.txt            # httpx, fastapi, openai
├── frontend/                       # Streamlit DeepSim Lab
├── workers/                        # Digital Twin Worker (worker.py)
└── docker-compose.yml              # Cluster Tanımı
```

---

*Powered by io.net Intelligence API & OpenAI LLMs*
