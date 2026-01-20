import streamlit as st
import requests
import pandas as pd
import time
import plotly.express as px
import os

# Backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.set_page_config(page_title="DeepSim Lab v3.2", layout="wide")

# Custom CSS for that "Premium" feel and Health Bars
st.markdown("""
<style>
    .stProgress > div > div > div > div {
        background-color: #00ce7c;
    }
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
    }
    .metric-card {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
    }
    div[data-testid="stExpander"] details summary {
        background-color: #2b2b2b !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔬 DeepSim Lab: Component Digital Twin")

# Initialize Session State for Savings
if "total_savings" not in st.session_state:
    st.session_state["total_savings"] = 0.0

# Sidebar
st.sidebar.header("Control Tower")
refresh_rate = st.sidebar.slider("Refresh Rate (s)", 1, 10, 2)

# SAVINGS COUNTER (The WOW Factor)
st.sidebar.markdown("---")
st.sidebar.subheader("💰 Est. Monthly Waste Saved")
st.sidebar.markdown(f"<h1 style='color: #00ce7c;'>${st.session_state['total_savings']:,.2f}</h1>", unsafe_allow_html=True)
st.sidebar.caption("Cumulative waste prevented by agents")

st.sidebar.markdown("---")
auto_pilot = st.sidebar.toggle("🛡️ ACTIVE WATCHDOG (Auto-Pilot)", value=False)
if auto_pilot:
    st.sidebar.success("Auto-Pilot ENGAGED")
else:
    st.sidebar.warning("Auto-Pilot DISENGAGED")

# Main Dashboard
tab1, tab2, tab3 = st.tabs(["🧬 Engineering Cockpit", "🤖 VRAM Oracle (Preserved)", "📜 System Logs"])

with tab1:
    st.markdown("### 🌡️ Real-Time Digital Twin Telemetry")
    
    # 1. Fetch & Display Workers with DeepSim Controls
    try:
        response = requests.get(f"{BACKEND_URL}/status", timeout=5)
        workers = response.json()
        
        if workers:
            cols = st.columns(len(workers))
            for idx, (wid, details) in enumerate(workers.items()):
                data = details.get('data', {})
                health = data.get('health', {})
                
                with cols[idx]:
                    st.success(f"📟 {wid.upper()}")
                    
                    # Physics Metrics
                    temp = data.get('temperature', 0)
                    fan = data.get('fan_speed', 0)
                    clock = data.get('clock_speed', 100)
                    lat = data.get('latency', 0)
                    
                    c1, c2 = st.columns(2)
                    c1.metric("Temp", f"{temp:.1f}°C", delta=f"{fan:.0f}% Fan", delta_color="off")
                    c2.metric("Clock", f"{clock:.0f}%", delta=f"Lat: {lat:.3f}s", delta_color="inverse")
                    
                    st.divider()
                    
                    # Health Bars
                    h_cool = health.get('cooling', 1.0)
                    h_net = health.get('network', 1.0)
                    
                    st.caption(f"❄️ Fan Integrity ({int(h_cool*100)}%)")
                    st.progress(h_cool)
                    
                    st.caption(f"🌐 Link Quality ({int(h_net*100)}%)")
                    st.progress(h_net)
                    
                    # DeepSim Sabotage Controls
                    with st.expander("🛠️ Engineering Tools", expanded=True):
                        # Sabotage: Cut Fan Wire
                        if st.button("✂️ Cut Fan Wire", key=f"cut_{wid}", use_container_width=True):
                            requests.post(f"{BACKEND_URL}/chaos/inject/{wid}", 
                                          json={"component": "COOLING", "health": 0.0})
                            st.toast(f"Executed: Fan Wire Cut on {wid}!")
                            
                        # Sabotage: Damage Port
                        if st.button("🔨 Damage Port", key=f"dmg_{wid}", use_container_width=True):
                             requests.post(f"{BACKEND_URL}/chaos/inject/{wid}", 
                                          json={"component": "NETWORK", "health": 0.5})
                             st.toast(f"Executed: Port Damaged on {wid}!")
                        
                        # Repair
                        if st.button("🧰 Repair Kit (Restore)", key=f"fix_{wid}", type="primary", use_container_width=True):
                            requests.post(f"{BACKEND_URL}/chaos/repair/{wid}")
                            st.toast(f"Restoring {wid} to factory health...")

        else:
            st.warning("No workers connected. Start a worker container.")
            
    except Exception as e:
        st.error(f"System Error: {e}")

    st.markdown("---")
    
    # Agentic Scan UI (Updated for Physics)
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🕵️ Physics-Aware Agent Team")
        if st.button("RUN DEEP DIAGNOSTICS", use_container_width=True, type="primary"):
            status_text = st.empty()
            progress_bar = st.progress(0)
            
            try:
                # 1. Watchdog
                status_text.markdown("**👁️ Watchdog:** Measuring thermodynamic deviations...")
                progress_bar.progress(25)
                time.sleep(0.5) 
                
                res = requests.post(f"{BACKEND_URL}/analyze/agentic-scan")
                
                if res.status_code == 200:
                    result = res.json()
                    logs = result.get("logs", [])
                    
                    # 2. Diagnostician
                    status_text.markdown("**🩺 Diagnostician:** Correlating physical anomalies...")
                    progress_bar.progress(50)
                    time.sleep(0.5)
                    
                    # 3. Accountant
                    status_text.markdown("**💸 Accountant:** Calculating thermal waste ($)...")
                    progress_bar.progress(75)
                    time.sleep(0.5)
                    
                    # 4. Enforcer
                    status_text.markdown("**🛡️ Enforcer:** Dispatching digital repair technicians...")
                    progress_bar.progress(100)
                    time.sleep(0.5)
                    
                    status_text.success("Diagnostics Complete!")
                    
                    # Display "Story"
                    with col2:
                        st.markdown("### 📝 Mission Report")
                        for log in logs:
                            agent = log['agent_id'].capitalize()
                            msg = log['message']
                            icon = "🔹"
                            if agent == "Watchdog": icon = "👁️"
                            elif agent == "Diagnostician": icon = "🩺"
                            elif agent == "Accountant": icon = "💸"
                            elif agent == "Enforcer": icon = "🛡️"
                            
                            with st.expander(f"{icon} {agent}", expanded=True):
                                st.write(msg)
                                if agent == "Accountant" and "data" in log:
                                     data = log["data"]
                                     if "total_waste_hourly" in data:
                                         waste = data["total_waste_hourly"]
                                         st.session_state['total_savings'] += (waste * 1.0) # Assume we save 1 hour of waste
                                         st.metric("Waste Identified", f"${waste:.2f}/hr")
                                         st.rerun()

                else:
                    st.error(f"Agent Failure: {res.text}")
                    
            except Exception as e:
                st.error(f"Workflow Failed: {e}")

with tab2:
    st.header("🔮 Agentic VRAM Oracle (v3.0 - Preserved)")
    st.markdown("Upload your training script (`.py`). Our **Hardware Architect Agents** will analyze it.")
    
    uploaded_file = st.file_uploader("Upload Python Script", type=["py"])
    
    if uploaded_file is not None:
        file_content = uploaded_file.getvalue().decode("utf-8")
        st.code(file_content[:500] + "...", language="python")
        
        if st.button("Start AI Analysis"):
            status_box = st.status("🧠 Agents working...", expanded=True)
            try:
                status_box.write("📤 Uploading code to backend...")
                res = requests.post(
                    f"{BACKEND_URL}/analyze/vram-agentic", 
                    params={"file_content": file_content},
                    timeout=120 
                )
                
                if res.status_code == 200:
                    data = res.json()
                    status_box.update(label="✅ Analysis Complete!", state="complete", expanded=False)
                    
                    metadata = data.get("metadata", {})
                    vram = data.get("vram", {})
                    advice = data.get("advice", "")
                    logs = data.get("logs", [])
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Model", metadata.get("model", "Unknown"))
                    c2.metric("Precision", metadata.get("precision", "Unknown"))
                    c3.metric("Batch Size", metadata.get("batch_size", "Unknown"))
                    c4.metric("Optimizer", metadata.get("optimizer", "Unknown"))
                    
                    st.divider()
                    
                    total_gb = vram.get("total_gb", 0)
                    st.markdown(f"<h1 style='text-align: center; color: #00ce7c;'>{total_gb} GB VRAM Required</h1>", unsafe_allow_html=True)
                    
                    if advice:
                         st.info(f"💡 **Optimization Advice:** {advice}")
                         
                    st.subheader("🕵️ Chain of Thought")
                    for log in logs:
                        agent = log['agent_id'].upper()
                        msg = log['message']
                        icon = "🤖"
                        if "PARSER" in agent: icon = "🧩"
                        elif "CALCULATOR" in agent: icon = "🧮"
                        elif "ADVISOR" in agent: icon = "💡"
                        
                        with st.chat_message(name=agent, avatar=icon):
                            st.write(f"**{agent}**: {msg}")
                else:
                    status_box.update(label="❌ Analysis Failed", state="error")
                    st.error(f"Backend Error: {res.text}")
            except Exception as e:
                status_box.update(label="❌ Error", state="error")
                st.error(f"Request Error: {e}")

with tab3:
    st.header("📜 Live System Logs")
    if st.button("Refresh Logs"): pass
    try:
        log_res = requests.get(f"{BACKEND_URL}/logs?lines=100")
        if log_res.status_code == 200:
            st.code("".join(log_res.json().get("logs", [])), language="log")
    except:
        st.error("Log fetch failed.")



# Auto-Pilot Logic
if auto_pilot:
    try:
        # Run scan every refresh cycle (simplified)
        requests.post(f"{BACKEND_URL}/analyze/agentic-scan", timeout=5)
    except Exception:
        pass # Don't block UI

time.sleep(refresh_rate)
st.rerun()
