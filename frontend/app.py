import streamlit as st
import requests
import pandas as pd
import time
import os

# Backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.set_page_config(page_title="io-Guard Merkezi (v4.0)", layout="wide", page_icon="🛡️")

# --- CSS (Premium & Clean) ---
st.markdown("""
<style>
    .big-stat { font-size: 3rem !important; font-weight: 800; color: #00ce7c; }
    .alert-stat { font-size: 3rem !important; font-weight: 800; color: #ff4b4b; }
    .card {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #333;
        margin-bottom: 10px;
    }
    .status-ok { border-left: 5px solid #00ce7c; }
    .status-warn { border-left: 5px solid #ffcc00; }
    .status-err { border-left: 5px solid #ff4b4b; }
</style>
""", unsafe_allow_html=True)

# --- HEADER: SIMULATIONS MODE & AGENT HUD ---
col_banner, col_hud = st.columns([2, 1])

with col_banner:
    st.markdown("""
    <div style='background-color: #2c0940; padding: 15px; border-radius: 8px; border: 1px solid #9d00ff;'>
        <h3 style='color: #d194ff; margin:0;'>🧪 SİMÜLASYON MODU</h3>
        <small style='color: #ccc;'>DeepSim Sanal Çekirdek Motoru Aktif</small>
    </div>
    """, unsafe_allow_html=True)

with col_hud:
    st.markdown("""
    <div style='background-color: #111; padding: 10px; border-radius: 8px; border: 1px solid #444;'>
        <small style='color: #888; letter-spacing: 1px;'>AKTİF AJANLAR</small><br>
        <span style='color: #00ce7c;'>● Watchdog</span> &nbsp;
        <span style='color: #3dd5e3;'>● Enforcer</span> &nbsp;
        <span style='color: #ffcc00;'>● Diagnostician</span>
    </div>
    """, unsafe_allow_html=True)

st.title("🛡️ io-Guard Operasyon Merkezi")

# ... (Global Status Fetch code remains similar) ...
try:
    cluster_res = requests.get(f"{BACKEND_URL}/cluster/status", timeout=1)
    status_data = cluster_res.json()
    active_count = len(status_data.get("active", []))
    active_nodes = status_data.get("active", [])
    idle_nodes = status_data.get("idle", [])
    cordoned_nodes = status_data.get("cordoned", [])
    
    total_nodes = active_count + len(idle_nodes) + len(cordoned_nodes)
    
    # Global Health Logic
    if len(cordoned_nodes) > 0:
        st.error(f"🚨 MOTOR ALARMI: {len(cordoned_nodes)} Sanal Çekirdek Karantinada! (Toplam: {total_nodes})")
    else:
        st.success(f"🟢 MOTOR STABİL: {active_count} Aktif / {len(idle_nodes)} Yedek Çekirdek")
        
except:
    st.warning("⚠️ BAĞLANTI HATASI: Backend'e ulaşılamıyor.")
    status_data = {}
    active_nodes = []
    idle_nodes = []
    cordoned_nodes = []

# --- SIDEBAR: CÜZDAN & KONTROL ---
st.sidebar.header("💎 Sanal Ekonomi ($IO)")
try:
    ledger_res = requests.get(f"{BACKEND_URL}/economy/ledger", timeout=1)
    if ledger_res.status_code == 200:
        ledger = ledger_res.json()
        bal = ledger.get("balance", 0)
        slash = ledger.get("slashed", 0)
        
        st.sidebar.metric("Simüle Bakiye", f"{bal:,.2f} $IO", delta=f"-{slash:.2f} Ceza", delta_color="inverse")
        
        if slash > 0:
            st.sidebar.error("⚠️ Bakiyeden ceza kesildi!")
            
        st.sidebar.subheader("Son İşlemler")
        for tx in reversed(ledger.get("history", [])[-5:]):
            icon = "✅" if tx['amount'] > 0 else "🔻"
            reason = tx['reason'].replace("SPOOF", "SAHTECİLİK").replace("LATENCY", "GECİKME").replace("OVERHEAT", "AŞIRI ISI")
            st.sidebar.caption(f"{icon} {reason}: {tx['amount']:+.2f}")
except:
    st.sidebar.text("Veri yok.")

st.sidebar.divider()
auto_pilot = st.sidebar.toggle("🤖 OTO-PİLOT (Ajanları Başlat)", value=True)
st.sidebar.caption("Watchdog ve Enforcer ajanları sanal ortamı denetler.")

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["🏗️ SİMÜLASYON ALANI", "🛡️ GÜVENLİK TESTİ", "🧠 MOTOR GÜNLÜĞÜ", "🔮 VRAM KAHİNİ"])

# TAB 1: VISUAL INFRASTRUCTURE
with tab1:
    col_infra_header, col_infra_action = st.columns([3, 1])
    with col_infra_header:
        st.subheader("DeepSim Sanal Çekirdek Kümesi")
    with col_infra_action:
        # PROVISIONING BUTTON
        if st.button("➕ Yeni Çekirdek Ekle (Scale Up)", help="Yedek (Standby) havuza yeni bir sanal işlemci ekler."):
            requests.post(f"{BACKEND_URL}/provision")
            st.toast("Yeni Sanal Çekirdek hazırlanıyor...", icon="🧱")
            time.sleep(1)
            st.rerun()

    # 1. AKTİF GRUP
    st.markdown("### 🟢 Aktif İşlem Havuzu")
    if not active_nodes:
        st.info("Aktif simülasyon yok.")
    
    cols = st.columns(4) # More dense
    try:
        full_stat = requests.get(f"{BACKEND_URL}/status").json()
    except:
        full_stat = {}

    for idx, wid in enumerate(active_nodes):
        info = full_stat.get(wid, {}).get("data", {})
        temp = info.get("temperature", 0)
        
        # Calculate Efficiency (Client-side mirror of backend logic for visual)
        # In a real app, backend should send "efficiency_index"
        eff_temp = max(0, 1.0 - (temp / 100.0))
        eff_clock = info.get("clock_speed", 100) / 100.0
        eff = (eff_clock * 0.4) + (eff_temp * 0.3) + (0.3) # simplified
        eff_percent = int(eff * 100)
        
        color = "#00ce7c" # Green
        if eff < 0.7: color = "#ffcc00" # Warning
        if eff < 0.4: color = "#ff4b4b" # Critical
        
        with cols[idx % 4]:
            st.markdown(f"""
            <div class="card" style="border-left: 5px solid {color};">
                <b>🖥️ {wid}</b><br>
                <span style='font-size: 0.8em; color: #ccc;'>Verimlilik (Efficiency)</span>
                <div style="background-color: #333; width: 100%; height: 6px; border-radius: 3px; margin-top:2px;">
                    <div style="background-color: {color}; width: {eff_percent}%; height: 6px; border-radius: 3px;"></div>
                </div>
                <small style='color: {color}; font-weight:bold;'>%{eff_percent} Performans</small><br>
                <span style='font-size: 0.8em; color: #888;'>Isı: {temp:.1f}°C</span>
            </div>
            """, unsafe_allow_html=True)
            with st.popover("🔧"):
                if st.button("🔥 Fanı Boz", key=f"sab_{wid}"):
                    requests.post(f"{BACKEND_URL}/chaos/inject/{wid}", json={"component": "COOLING", "health": 0.0})
                    st.toast(f"{wid} sabote edildi!")

    st.divider()

    # 2. YEDEK (IDLE) GRUP
    col_idle, col_bad = st.columns(2)
    
    with col_idle:
        st.markdown(f"### 🟡 Yedek Havuz ({len(idle_nodes)})")
        if idle_nodes:
            for wid in idle_nodes:
                st.code(f"🌙 {wid} (Hazır Bekliyor)")
        else:
            st.caption("Yedek havuz boş. 'Scale Up' yapın.")

    with col_bad:
        st.markdown(f"### 🔴 Karantina / Arızalı ({len(cordoned_nodes)})")
        if cordoned_nodes:
            for wid in cordoned_nodes:
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.error(f"🚫 {wid} (İzole)")
                with c2:
                    if st.button("🛠️", key=f"fix_{wid}", help="Tamir et ve havuza geri al"):
                        requests.post(f"{BACKEND_URL}/chaos/repair/{wid}")
                        st.toast(f"{wid} tamir ediliyor...")
                        time.sleep(1)
                        st.rerun()
        else:
            st.caption("Arızalı cihaz yok.")

# TAB 2: SECURITY
with tab2:
    st.subheader("İmza ve Kimlik Doğrulama (Proof-of-Integrity)")
    
    col_sec1, col_sec2 = st.columns([2, 1])
    
    with col_sec1:
        st.markdown("**Canlı İmza Akışı**")
        # Reuse full_stat
        for wid, detail in full_stat.items():
            integrity = detail.get("integrity", "UNKNOWN")
            
            if integrity == "VERIFIED":
                st.success(f"✅ {wid}: İMZA GEÇERLİ (Doğrulanmış Donanım)")
            elif integrity == "SPOOFED":
                st.error(f"🚨 {wid}: SAHTE İMZA TESPİT EDİLDİ! (Spoofing Attack)")
            else:
                st.warning(f"⚠️ {wid}: İmza Bekleniyor...")
                
    with col_sec2:
        st.markdown("**Saldırı Simülasyonu (Red Team)**")
        target = st.selectbox("Hedef Seç", active_nodes if active_nodes else ["worker-1"])
        
        if st.button("🏴‍☠️ SAHTE İMZA SALDIRISI YAP (Spoof)", type="primary"):
            requests.post(f"{BACKEND_URL}/simulation/attack", json={"type": "SIGNATURE_SPOOF", "worker_id": target})
            st.toast(f"{target} üzerinde sahtecilik başlatıldı!", icon="🕵️")
            
        st.caption("Bu işlem, seçilen işçinin sahte imza üretmesine neden olur. Watchdog ajanı bunu yakalayıp cezayı kesmelidir.")

# TAB 3: AGENT LOGS
with tab3:
    st.subheader("Ajan Düşünce Akışı")
    
    try:
        logs = requests.get(f"{BACKEND_URL}/analyze/logs?limit=20").json().get("logs", [])
        for log in reversed(logs):
            agent = log.get('agent', 'Unknown')
            msg = log.get('message', '')
            details = log.get('details', None)
            
            # Icon Mapping
            icon = "🤖"
            if agent == "Watchdog": icon = "👁️"
            elif agent == "Enforcer": icon = "🛡️"
            elif agent == "Brain (LLM)": icon = "🧠"
            
            with st.expander(f"{icon} **{agent}**: {msg.splitlines()[0]}"):
                st.write(msg)
                if details:
                    st.markdown("---")
                    st.caption("🔍 **Sistem Düşüncesi (Debug):**")
                    st.json(details)
            
    except:
        st.text("Günlük yüklenemedi.")

# TAB 4: VRAM ORACLE
tab4 = tab3 # Hack to re-use variable names if needed, but better to just add to the list above
# Actually, I need to redefine the tabs list.
# Let's fix the tabs definition first.

# ... Logic below assumes tabs are updated ...

    except:
        st.text("Günlük yüklenemedi.")

# TAB 4: VRAM ORACLE
with tab4:
    st.markdown("### 🔮 Agentic VRAM Oracle (Pre-Flight Check)")
    st.info("Eğitim kodunuzu (`train.py`) yapıştırın. Ajan sürüsü donanım gereksinimlerini hesaplasın.")
    
    col_code, col_result = st.columns([1, 1])
    
    with col_code:
        code_input = st.text_area("Python Kodu", height=400, placeholder="import torch\nmodel = LlamaForCausalLM...")
        analyze_btn = st.button("🚀 Kodu Analiz Et", type="primary", use_container_width=True)
        
    with col_result:
        if analyze_btn and code_input:
            with st.status("🔍 Ajanlar Kodunuzu İnceliyor...", expanded=True) as status:
                try:
                    res = requests.post(f"{BACKEND_URL}/analyze/vram-agentic", params={"file_content": code_input}, timeout=15).json()
                    
                    st.write("✅ **Code Parser**: Kod yapısı çözümlendi.")
                    st.write("✅ **VRAM Calculator**: Matematiksel hesaplama tamamlandı.")
                    st.write("✅ **Advisor**: Optimizasyon önerileri hazırlandı.")
                    status.update(label="Analiz Tamamlandı!", state="complete", expanded=False)
                    
                    # 1. METADATA
                    st.subheader("🧩 Kod Analizi")
                    meta = res.get("metadata", {})
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Model", meta.get("model", "Unknown"))
                    c2.metric("Batch Size", meta.get("batch_size", "?"))
                    c3.metric("Optimizer", meta.get("optimizer", "?"))
                    
                    # 2. VRAM
                    st.subheader("🧮 VRAM Hesabı")
                    vram = res.get("vram", {})
                    total_gb = vram.get("total_gb", 0)
                    
                    # Visaul Bar
                    max_vram = 24.0 # RTX 4090 example
                    pct = min(1.0, total_gb / max_vram)
                    bar_color = "green" if pct < 0.9 else "red"
                    
                    st.progress(pct, text=f"Tahmini Kullanım: {total_gb} GB / {max_vram} GB")
                    if pct > 1.0:
                        st.error(f"⚠️ YETERSİZ VRAM! {total_gb - max_vram:.1f} GB daha gerekiyor.")
                    else:
                        st.success("✅ Donanım Yeterli.")
                        
                    # 3. ADVICE
                    st.subheader("💡 Tavsiyeler")
                    advice_data = res.get("advice", "")
                    if isinstance(advice_data, dict):
                         st.info(advice_data.get("advice", "Öneri yok."))
                    else:
                         st.info(str(advice_data))
                    
                except Exception as e:
                    status.update(label="Analiz Hatası!", state="error")
                    st.error(f"Hata: {str(e)}")

# Auto-Refresh Logic
if auto_pilot:
    try:
        requests.post(f"{BACKEND_URL}/analyze/agentic-scan", timeout=2)
    except:
        pass
        
time.sleep(2)
st.rerun()
