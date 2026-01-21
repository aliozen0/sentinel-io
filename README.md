# 🛡️ io-Guard: Agentic FinOps Orchestrator (v4.0)

> **"Gerçekçilik ile Zeka Birleşti: Hibrit Operasyon Dönemi"**

**io-Guard v4.0**, io.net ekosistemi için tasarlanmış, **Termodinamik Fizik Motoru (DeepSim)** ve **Hibrit Yapay Zeka (Hybrid-AI)** üzerine kurulu, otonom bir FinOps yönetim platformdur.

Bu sürümde ("Intelligence Update"), sistem sadece hata olduğunda değil, **verimlilik düştüğünde de** müdahale eden proaktif bir yapıya kavuşmuştur.

---

## 🧠 v4.0: Hibrit Zeka & Beyin İzi (Brain Trace)

Artık ajanların ne düşündüğünü tahmin etmenize gerek yok. **Şeffaflık Modu** ile her kararın arkasındaki mantığı (Prompt/Response) canlı izleyebilirsiniz.

| Özellik | Açıklama |
| :--- | :--- |
| **Hybrid Watchdog** | Sadece "Sıcak/Soğuk" demez. Her node için **Efficiency Index (0.0 - 1.0)** hesaplar. Matematiksel tespiti, LLM muhakemesiyle birleştirir. |
| **Brain Trace** 🧠 | LLM'e giden komutları ve gelen cevapları arayüzde **"Düşünce Balonu"** olarak gösterir. Hataları ve kararları şeffaflaştırır. |
| **Preemptive Failover** | Enforcer Ajanı, cihaz bozulmadan **önce** müdahale eder. Verimlilik %70'in altına düştüğünde, kullanıcı deneyimini korumak için "Sağlıklı Yedek" ile "Yorgun İşçiyi" değiştirir. |

---

## 🌪️ DeepSim Physics Engine & Digital Twins

Sistem, donanımları yüzeysel değil, fiziksel parametrelerle simüle eder:

| Bileşen | Simülasyon Özelliği | Etki |
| :--- | :--- | :--- |
| **Efficiency (WEI)** | 📊 Weighted Efficiency Index | Clock Hızı, Isı ve Log-Latency verilerinden oluşan canlı karne notu. |
| **Cooling** | ❄️ Thermodynamic Loop | Fan RPM, Isı (Temp), Soğutma Kapasitesi. |
| **Logic** | 🧠 Throttling | Verimlilik düştüğünde (%60 altı) sistem otomatik olarak "Performans Kaybı" alarmı verir. |

---

## 🤖 The Smart Agent Swarm

Ajanlar artık "Kural Tabanlı" değil, "Veri Odaklı Karar Verici" (Data-Driven Decision Makers) konumundadır.

| Simge | Ajan | Yeni Süper Gücü |
| :--- | :--- | :--- |
| 👁️ | **Watchdog** | **Efficiency Auditor**: "Sıcaklık normal ama Clock hızı düşük -> Verimlilik %65. Bu kabul edilemez!" diyerek alarm verir. |
| 🩺 | **Diagnostician** | **Root Cause Analysis**: Sorunun kaynağını (Fan Motoru, Termal Macun, Ağ Darboğazı) teşhis eder. |
| 💸 | **Accountant** | **Real-Time Ledger**: Her aksiyonun maliyetini (Cost of Repair vs Cost of Downtime) hesaplar. |
| 🛡️ | **Enforcer** | **SLA Guardian**: Kullanıcı deneyimini (SLA) korumak için gerekirse çalışan (ama yavaş) makineyi kapatıp, yedeği devreye sokar. |

---

## 🔮 Agentic VRAM Oracle (Pre-Flight Check)

IO.net ekosisteminde en çok karşılaşılan "Out of Memory (OOM)" hatalarını önlemek için geliştirdiğimiz **3 Aşamalı Kod Denetim Hattı**:

1.  **🧩 Code Parser Agent**: Yüklenen Python eğitim kodunu analiz eder (Model, Batch Size, Optimizer).
2.  **🧮 VRAM Calculator**: Gerekli VRAM miktarını **GB cinsinden hesaplar**.
3.  **💡 Optimization Advisor**: Mevcut donanım yetersizse, *Gradient Accumulation*, *LoRA* gibi teknik tavsiyeler verir.

---

## 💻 DeepSim Lab: Operasyon Merkezi

Yeni **Türkçe Arayüz** ile tam hakimiyet:

*   **Canlı Verimlilik Barları**: Her kartın performansını renkli barlarla (Yeşil/Sarı/Kırmızı) izleyin.
*   **Motor Günlüğü (Brain Trace)**: Ajanların "Thinking..." süreçlerini okuyun.
*   **Dinamik Ölçekleme**: "Yeni Çekirdek Ekle" butonu ile yedek havuzunu büyütün.
*   **Sabotaj Modu**: "Fanı Boz" diyerek ajanların kriz yönetimini test edin.

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

1.  Arayüzden **"Yeni Çekirdek Ekle"** ile yedek havuza işçi ekleyin.
2.  Aktif bir karta **"🔧 -> 🔥 Fanı Boz"** deyin.
3.  **İzleyin:**
    *   Kartın **Verimlilik Barı** düşmeye başlayacak.
    *   %70 altına inince bar sararacak, Watchdog **"Performans Kaybı"** raporlayacak.
    *   **Enforcer Ajanı**, kart bozulmadan önce (Preemptive Failover) onu yedeğe çekecek ve taze bir işçiyi işe alacak.
    *   Tüm bu süreci **"Motor Günlüğü"**ndeki 🧠 ikonlarına tıklayarak okuyabilirsiniz.

---

## 🏗️ Teknik Mimari & Altyapı (Core Features)

Buzdağının görünen yüzü arayüz olsa da, suyun altında şu sistemler çalışmaktadır:

### 1. Security Core (Proof-of-Compute) 🔒
*   **HMAC-SHA256 Signatures**: Her Worker, ürettiği telemetri verisini (Latency, GPU Temp) gizli anahtarı ile imzalar.
*   **Tamper-Proofing**: Watchdog ajanı, imzası geçersiz veya bozuk olan paketleri "SPOOFING" olarak işaretler ve reddeder.
*   **Endpoint:** `/telemetry/secure`

### 2. Ray-Lite Orchestrator ⚡
*   **Lifecycle Management**: Node'lar sadece "Açık/Kapalı" değildir. `IDLE` (Yedek), `ACTIVE` (Çalışan), `CORDONED` (Karantina), `DRAINING` (Kapatılıyor) durumları arasında geçiş yaparlar.
*   **State Manager**: Tüm küme durumu bellekte (In-Memory) tutulur ve nanosaniye hızında yönetilir.
*   **Endpoint:** `/cluster/status`

### 3. Economy Engine (Tokenomics) 💎
*   **Accountant Agent**: Sistemin CFO'sudur.
*   **Ledger**: Her milisaniyede bir "Compute Cost" hesaplar. Kesintilerde (SLA Breach) "Slashing" (Ceza) keser, başarılı işlerde "Reward" (Ödül) dağıtır.
*   **Endpoint:** `/economy/ledger`

---

## 📂 Proje Yapısı

```plaintext
io-guard/
├── backend/
│   ├── agents/                     # Hibrit AI Ajanları (Watchdog, Enforcer...)
│   ├── services/                   # State Manager & Simulation Logic
│   ├── ai_client.py                # OpenAI Wrapper & Brain Trace Logging
│   ├── main.py                     # API Endpoints
│   └── requirements.txt            
├── frontend/                       # Streamlit Dashboard (Türkçe)
├── workers/                        # Digital Twin Worker (worker.py)
└── docker-compose.yml              # Cluster Tanımı
```

---

*Powered by io.net Intelligence API & OpenAI LLMs*
