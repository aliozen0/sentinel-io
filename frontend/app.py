import streamlit as st
import requests
import pandas as pd
import time
import plotly.express as px
import os

# Backend URL - use service name in Docker, or localhost for local dev if not in container
# But since this runs in Docker, it should use the container name 'backend'
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.set_page_config(page_title="io-Guard Dashboard", layout="wide")

st.title("🚀 io-Guard: Autonomous Compute Orchestrator")

# Sidebar
st.sidebar.header("Control Panel")
refresh_rate = st.sidebar.slider("Refresh Rate (s)", 1, 10, 2)

# Main Dashboard
col1, col2 = st.columns(2)

with col1:
    st.subheader("📡 Cluster Health")
    # Fetch status
    try:
        response = requests.get(f"{BACKEND_URL}/status", timeout=5)
        workers = response.json()
        
        # Determine metrics
        active_count = sum(1 for w in workers.values() if w['status'] == 'Active')
        total_workers = len(workers)
        
        st.metric("Active Nodes", f"{active_count}/{total_workers}")
        
        # Display DataFrame
        if workers:
            df_data = []
            for wid, details in workers.items():
                data = details.get('data', {})
                df_data.append({
                    "Worker ID": wid,
                    "Status": details.get('status'),
                    "Latency (s)": f"{data.get('latency', 0):.4f}",
                    "GPU Util (%)": data.get('gpu_util', 0),
                    "Temp (°C)": data.get('temperature', 0)
                })
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
            
        else:
            st.info("No active workers detected.")

    except Exception as e:
        st.error(f"Connection Error: {e}")
        workers = {}

with col2:
    st.subheader("🧠 io Intelligence Actions")
    
    # Pre-Flight Oracle
    st.markdown("#### Pre-Flight Oracle (VRAM Prediction)")
    uploaded_file = st.file_uploader("Upload Training Script (train.py)", type=["py"])
    if uploaded_file is not None:
        content = uploaded_file.getvalue().decode("utf-8")
        if st.button("Analyze Code Requirements"):
            with st.spinner("Asking AI..."):
                try:
                    res = requests.post(f"{BACKEND_URL}/analyze/vram-prediction", params={"file_content": content})
                    if res.status_code == 200:
                        st.json(res.json())
                    else:
                        st.error(f"Error: {res.text}")
                except Exception as e:
                    st.error(f"Request failed: {e}")

    # Straggler Detection
    st.markdown("#### In-Flight Anomaly Detection")
    if st.button("Scan for Stragglers"):
        with st.spinner("Analyzing Cluster Telemetry..."):
            try:
                res = requests.post(f"{BACKEND_URL}/analyze/stragglers")
                if res.status_code == 200:
                    result = res.json()
                    if "killed" in result.get("result", "").lower():
                        st.warning(result["result"])
                    else:
                        st.success(result["result"])
                    with st.expander("AI Raw Response"):
                        st.write(result.get("ai_raw"))
                else:
                    st.error(f"Error: {res.text}")
            except Exception as e:
                st.error(f"Request failed: {e}")

# Live Charts
if workers:
    st.subheader("📈 Real-time Telemetry")
    # For simplicity, just plotting last fetched latency snapshot
    # Ideally, we'd keep history in frontend session_state or fetch history from backend
    
    df_chart = pd.DataFrame([
        {"Worker": wid, "Latency": details['data'].get('latency', 0)} 
        for wid, details in workers.items() if details['status'] == 'Active'
    ])
    
    if not df_chart.empty:
        fig = px.bar(df_chart, x="Worker", y="Latency", color="Latency", title="Current Latency per Worker")
        st.plotly_chart(fig, use_container_width=True)

time.sleep(refresh_rate)
st.rerun()
