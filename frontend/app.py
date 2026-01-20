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
tab1, tab2 = st.tabs(["🚀 Mission Control", "📜 System Logs"])

with tab1:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📡 Cluster Telemetry")
        # Fetch status
        try:
            response = requests.get(f"{BACKEND_URL}/status", timeout=5)
            workers = response.json()
            
            # Metrics
            active_count = sum(1 for w in workers.values() if w['status'] == 'Active')
            total_workers = len(workers)
            st.metric("Active Nodes", f"{active_count}/{total_workers}")
            
            # DataFrame
            if workers:
                df_data = []
                for wid, details in workers.items():
                    data = details.get('data', {})
                    df_data.append({
                        "Worker ID": wid,
                        "Status": details.get('status'),
                        "Latency (s)": f"{data.get('latency', 0):.4f}",
                        "Temp (°C)": f"{data.get('temperature', 0):.1f}",
                        "GPU Util (%)": data.get('gpu_util', 0)
                    })
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No active workers detected.")

        except Exception as e:
            st.error(f"Connection Error: {e}")
            workers = {}

    with col2:
        st.subheader("🤖 Autonomous Agent Team")
        
        st.info("System is monitored by 4 specialist agents.")
        
        # Agentic Scan Button
        if st.button("RUN AGENTIC DIAGNOSTICS", use_container_width=True, type="primary"):
            status_text = st.empty()
            progress_bar = st.progress(0)
            
            try:
                # 1. Watchdog
                status_text.markdown("**👁️ Watchdog:** Scanning telemetry...")
                progress_bar.progress(25)
                time.sleep(0.5) # UI Effect
                
                # Call Backend for Full Scan (simulating steps for UI drama, but backend runs atomic)
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
                    
                    # Display "Story" from logs
                    st.markdown("### 📝 Mission Report")
                    
                    for log in logs:
                        agent = log['agent_id'].capitalize()
                        msg = log['message']
                        icon = "🔹"
                        if agent == "Watchdog": icon = "👁️"
                        elif agent == "Diagnostician": icon = "🩺"
                        elif agent == "Accountant": icon = "💸"
                        elif agent == "Enforcer": icon = "🛡️"
                        
                        with st.expander(f"{icon} {agent} Report", expanded=True):
                            st.write(msg)
                            if agent == "Accountant" and "data" in log:
                                data = log["data"]
                                if "story" in data:
                                    st.success(f"**Insight:** {data['story']}")
                                if "total_waste_hourly" in data:
                                    waste = data["total_waste_hourly"]
                                    # Update session state savings logic (Mock calculation for savings)
                                    # In reality, savings = waste prevented * hours
                                    st.session_state['total_savings'] += (waste * 720) # Monthly projection
                                    st.rerun()

                else:
                    st.error(f"Agent Failure: {res.text}")
                    
            except Exception as e:
                st.error(f"Workflow Failed: {e}")

    # Live Charts
    if workers:
        st.markdown("### 📈 Live Performance")
        df_chart = pd.DataFrame([
            {"Worker": wid, "Latency": details['data'].get('latency', 0)} 
            for wid, details in workers.items() if details['status'] == 'Active'
        ])
        if not df_chart.empty:
            fig = px.bar(df_chart, x="Worker", y="Latency", color="Latency", 
                        color_continuous_scale=["#00ce7c", "#ff4b4b"])
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("📜 Live System Logs")
    st.caption("Real-time trace of agent activities, IO Intelligence calls, and decisions.")
    
    if st.button("Refresh Logs"):
        # Just rerun to fetch new logs
        pass

    try:
        log_res = requests.get(f"{BACKEND_URL}/logs?lines=100")
        if log_res.status_code == 200:
            logs = log_res.json().get("logs", [])
            log_text = "".join(logs)
            st.code(log_text, language="log")
        else:
            st.error("Could not fetch logs.")
    except Exception as e:
        st.error(f"Log fetch error: {e}")

time.sleep(refresh_rate)
st.rerun()
