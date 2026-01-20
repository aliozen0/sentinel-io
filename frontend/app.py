import streamlit as st
import requests
import pandas as pd
import time
import plotly.express as px
import os

# Backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.set_page_config(page_title="io-Guard v2.0", layout="wide")

# Custom CSS for that "Premium" feel
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
</style>
""", unsafe_allow_html=True)

st.title("🛡️ io-Guard: Agentic FinOps Orchestrator")

# Initialize Session State for Savings
if "total_savings" not in st.session_state:
    st.session_state["total_savings"] = 0.0

# Sidebar
st.sidebar.header("Control Tower")
refresh_rate = st.sidebar.slider("Refresh Rate (s)", 1, 10, 2)

# SAVINGS COUNTER (The WOW Factor)
st.sidebar.markdown("---")
st.sidebar.subheader("💰 Est. Monthly Savings")
st.sidebar.markdown(f"<h1 style='color: #00ce7c;'>${st.session_state['total_savings']:,.2f}</h1>", unsafe_allow_html=True)
st.sidebar.caption("Cumulative waste prevented by agents")

# Main Dashboard
# Main Dashboard
tab1, tab2, tab3 = st.tabs(["🚀 Mission Control", "🤖 VRAM Oracle (v3.0)", "📜 System Logs"])

with tab1:
    st.markdown("### 🕹️ Dynamic Chaos Engine")
    
    # 1. Fetch & Display Workers with Chaos Controls
    try:
        response = requests.get(f"{BACKEND_URL}/status", timeout=2)
        workers = response.json()
        
        if workers:
            cols = st.columns(len(workers))
            for idx, (wid, details) in enumerate(workers.items()):
                with cols[idx]:
                    # Chaos Status Check
                    cmd_res = requests.get(f"{BACKEND_URL}/command/{wid}")
                    is_chaos = cmd_res.json().get("chaos", False) if cmd_res.status_code == 200 else False
                    
                    status_color = "red" if is_chaos else "green"
                    st.markdown(f"**{wid.upper()}**")
                    st.markdown(f"Status: <span style='color:{status_color}'>{'SABOTAGED' if is_chaos else 'Normal'}</span>", unsafe_allow_html=True)
                    
                    # Telemetry Sparklines (Mock or Real)
                    lat = details['data'].get('latency', 0)
                    st.metric("Latency", f"{lat:.2f}s", delta="-High" if is_chaos else "Normal", delta_color="inverse")
                    
                    # Controls
                    if is_chaos:
                        if st.button("🟢 RECOVER", key=f"rec_{wid}", use_container_width=True):
                            requests.post(f"{BACKEND_URL}/chaos/reset/{wid}")
                            st.rerun()
                    else:
                        if st.button("🔴 SABOTAGE", key=f"sab_{wid}", use_container_width=True):
                            requests.post(f"{BACKEND_URL}/chaos/inject/{wid}")
                            st.rerun()
        else:
            st.warning("No workers connected.")
            
    except Exception as e:
        st.error(f"System Error: {e}")

    st.markdown("---")
    
    # Existing Agentic Scan UI
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🤖 Agent Team")
        if st.button("RUN AGENTIC DIAGNOSTICS", use_container_width=True, type="primary"):
            status_text = st.empty()
            progress_bar = st.progress(0)
            
            try:
                # 1. Watchdog
                status_text.markdown("**👁️ Watchdog:** Scanning telemetry...")
                progress_bar.progress(25)
                time.sleep(0.5) 
                
                res = requests.post(f"{BACKEND_URL}/analyze/agentic-scan")
                
                if res.status_code == 200:
                    result = res.json()
                    logs = result.get("logs", [])
                    
                    # 2. Diagnostician
                    status_text.markdown("**🩺 Diagnostician:** Identifying root causes...")
                    progress_bar.progress(50)
                    time.sleep(0.5)
                    
                    # 3. Accountant
                    status_text.markdown("**💸 Accountant:** Calculating financial impact...")
                    progress_bar.progress(75)
                    time.sleep(0.5)
                    
                    # 4. Enforcer
                    status_text.markdown("**🛡️ Enforcer:** Applying fixes...")
                    progress_bar.progress(100)
                    time.sleep(0.5)
                    
                    status_text.success("Scan Complete!")
                    
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
                                         st.session_state['total_savings'] += (waste * 720) 
                                         st.rerun()

                else:
                    st.error(f"Agent Failure: {res.text}")
                    
            except Exception as e:
                st.error(f"Workflow Failed: {e}")

with tab2:
    st.header("🔮 Agentic VRAM Oracle")
    st.markdown("Upload your training script (`.py`). Our **Hardware Architect Agents** will analyze it.")
    
    # v3.1: File Uploader Support
    uploaded_file = st.file_uploader("Upload Python Script", type=["py"])
    
    if uploaded_file is not None:
        # Read file content
        file_content = uploaded_file.getvalue().decode("utf-8")
        st.code(file_content[:500] + "...", language="python")
        st.caption("Preview")
        
        if st.button("Start AI Analysis"):
            status_box = st.status("🧠 Agents working...", expanded=True)
            try:
                status_box.write("📤 Uploading code to backend...")
                # Increased timeout to 60s because AI takes time
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
                    
                    # 1. Visualization
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Model", metadata.get("model", "Unknown"))
                    c2.metric("Precision", metadata.get("precision", "Unknown"))
                    c3.metric("Batch Size", metadata.get("batch_size", "Unknown"))
                    c4.metric("Optimizer", metadata.get("optimizer", "Unknown"))
                    
                    st.divider()
                    
                    # 2. VRAM Result
                    total_gb = vram.get("total_gb", 0)
                    st.markdown(f"<h1 style='text-align: center; color: #00ce7c;'>{total_gb} GB VRAM Required</h1>", unsafe_allow_html=True)
                    
                    if advice:
                         st.info(f"💡 **Optimization Advice:** {advice}")
                         
                    # 3. Agent Thought Process (Chain of Thought)
                    st.subheader("🕵️ Chain of Thought (Backend Logs)")
                    for log in logs:
                        agent = log['agent_id'].upper()
                        msg = log['message']
                        # Color code agents
                        if "PARSER" in agent: icon = "🧩"
                        elif "CALCULATOR" in agent: icon = "🧮"
                        elif "ADVISOR" in agent: icon = "💡"
                        else: icon = "🤖"
                        
                        with st.chat_message(name=agent, avatar=icon):
                            st.write(f"**{agent}**: {msg}")
                            
                else:
                    status_box.update(label="❌ Analysis Failed", state="error")
                    st.error(f"Backend Error: {res.text}")
                    
            except requests.exceptions.Timeout:
                status_box.update(label="⚠️ Timeout", state="error")
                st.error("The AI agents are taking too long (>60s). Please try again or check System Logs.")
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


time.sleep(refresh_rate)
st.rerun()
