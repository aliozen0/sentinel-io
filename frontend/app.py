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

    # --- 🧪 SIMULATION SCENARIOS (Verification UI) ---
    st.markdown("---")
    st.subheader("🧪 Simulation Scenarios")
    
    with st.expander("🌪️ Scenario 1: The 'Slow Burn' (Dust Accumulation)", expanded=False):
        st.markdown("""
        **Objective:** Trigger "The Oracle" by simulating hidden dust buildup.
        **Transparency Protocol:**
        1. We will inject a `DUST_FACTOR` of 0.8 into the physics engine.
        2. You will see the **API Response** confirming the sabotage.
        3. We will wait 15s, printing real-time thermodynamics logs.
        4. We will send the `Time-Series CSV` to the Oracle Agent.
        """)
        
        if st.button("▶️ START LIVE EXPERIMENT", type="primary", use_container_width=True):
            console = st.empty()
            log_container = st.container()
            
            def log_step(msg):
                with log_container:
                    st.markdown(f"```bash\n> {msg}\n```")
                    time.sleep(0.3)

            try:
                # 1. Select Target
                console.info("🔍 Scanning Cluster for active nodes...")
                workers_res = requests.get(f"{BACKEND_URL}/status")
                workers_map = workers_res.json()
                if not workers_map:
                    console.error("❌ No workers found!")
                    st.stop()
                
                target_id = list(workers_map.keys())[0]
                console.success(f"🎯 Target Acquired: {target_id}")
                log_step(f"TARGET_LOCK: {target_id}")
                
                # 2. Inject Sabotage
                console.warning("🌪️ Injecting DUST SABOTAGE payload...")
                res = requests.post(f"{BACKEND_URL}/chaos/inject/{target_id}", 
                             json={"component": "DUST", "health": 0.8})
                log_step(f"POST /chaos/inject/{target_id} payload={{dust: 0.8}} -> {res.status_code}")
                
                # 3. Wait for Physics
                console.info("⏳ Collecting Thermodynamics Data (15s)...")
                prog = console.progress(0)
                
                metrics_placeholder = st.empty()
                
                for i in range(15):
                    # Fetch real-time data to show it's real
                    w_res = requests.get(f"{BACKEND_URL}/status")
                    if w_res.status_code == 200:
                        curr_data = w_res.json()[target_id]['data']
                        temp = curr_data['temperature']
                        fan = curr_data['fan_speed']
                        metrics_placeholder.caption(f"Physics State: Temp={temp:.1f}°C | Fan={fan:.1f}%")
                    
                    time.sleep(1)
                    prog.progress((i+1)/15)
                
                metrics_placeholder.empty()

                # 4. Trigger Scan
                console.info("👁️ transmitting Time-Series Vector to Oracle AI...")
                log_step("POST /analyze/agentic-scan (Payload: Last 60s Telemetry)")
                
                scan_res = requests.post(f"{BACKEND_URL}/analyze/agentic-scan")
                
                if scan_res.status_code == 200:
                    console.success("✅ Analysis Complete! Oracle has spoken.")
                    log_step("RESPONSE 200 OK: Oracle Prediction Received.")
                    time.sleep(1)
                    st.rerun() 
                else:
                    console.error(f"❌ Scan Failed: {scan_res.text}")
                    
            except Exception as e:
                console.error(f"Execution Error: {str(e)}")

    # -----------------------------------------------


    st.markdown("---")
    
    # --- 🧠 AGENT NEURAL STREAM (Automated & Visual) ---
    st.markdown("---")
    st.subheader("🧠 io Intelligence Neural Stream")
    
    # Initialize Session State for Logs
    if "agent_history" not in st.session_state:
        st.session_state["agent_history"] = []
        
    # Layout: Live Feed (Left) vs Meaningful Insights (Right)
    col_feed, col_insights = st.columns([1, 1])
    
    with col_feed:
        st.markdown("#### � Live Agent Protocol Feed")
        feed_container = st.container(height=400)
        
        # Display History (Reverse Order)
        for log in reversed(st.session_state["agent_history"]):
            with feed_container:
                 agent = log['agent']
                 msg = log['message']
                 ts = log.get('timestamp', '')
                 icon = "🔹"
                 color = "gray"
                 
                 if agent == "Watchdog": icon, color = "👁️", "#3dd5e3"
                 elif agent == "Oracle": icon, color = "🔮", "#9d00ff"
                 elif agent == "Diagnostician": icon, color = "🩺", "#ffcc00"
                 elif agent == "Accountant": icon, color = "💸", "#00ce7c"
                 elif agent == "Enforcer": icon, color = "🛡️", "#ff4b4b"
                 
                 st.markdown(f"""
                 <div style='border-left: 3px solid {color}; padding-left: 10px; margin-bottom: 10px;'>
                    <small style='color: #888;'>{ts}</small><br>
                    <strong>{icon} {agent}</strong>: {msg}
                 </div>
                 """, unsafe_allow_html=True)

    with col_insights:
        st.markdown("#### 💡 Key Decisions & Actions")
        # Filter for "Actionable" or "Important" logs
        important_logs = [l for l in st.session_state["agent_history"] 
                          if l['agent'] in ["Enforcer", "Oracle", "Diagnostician"] 
                          or "violation" in l['message']]
                          
        if not important_logs:
            st.info("System Stable. Agents standing by.")
        else:
            for log in reversed(important_logs[-5:]): # Show last 5 major events
                agent = log['agent']
                msg = log['message']
                # Card Style
                st.info(f"**{agent}**: {msg}", icon="⚡") 
                
                # Special Visuals for specific agents
                if agent == "Oracle" and "data" in log:
                     data = log['data']
                     if "predictions" in data:
                         preds = data["predictions"]
                         if preds: 
                             with st.expander("🔮 View Prediction Evidence"):
                                 st.json(preds)
                                 
                if agent == "Enforcer":
                    st.toast(f"Action Taken: {msg}")

    # AUTO-PILOT LOGIC (Background)
    # Always poll logs to update the Neural Stream (even if we didn't trigger the scan)
    try:
        # 1. Fetch Global Agent Logs
        log_res = requests.get(f"{BACKEND_URL}/analyze/logs?limit=50", timeout=2)
        if log_res.status_code == 200:
            st.session_state["agent_history"] = log_res.json().get("logs", [])
            
        # 2. Auto-Pilot Trigger (Only if enabled)
        if auto_pilot:
             requests.post(f"{BACKEND_URL}/analyze/agentic-scan", timeout=2)
             
    except Exception:
        pass # Fail silently in background loops

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



# Refresh Loop
time.sleep(refresh_rate)
st.rerun()
