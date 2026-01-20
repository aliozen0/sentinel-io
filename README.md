# 🚀 io-Guard: Autonomous Compute Orchestrator

**io-Guard** is a "Compute Resource Lifecycle Manager" developed for the io.net ecosystem. It uses **io Intelligence API** to solve inefficiencies and hardware incompatibilities in distributed GPU clusters.

## 🌟 Features

*   **Pre-Flight Oracle:** Predicts VRAM requirements for training jobs using AI.
*   **In-Flight Straggler Detection:** Uses AI to identify and eliminate slow nodes (Stragglers) in real-time.
*   **Simulation Mode:** Simulates a GPU cluster using Docker containers since actual IO Cloud access is paid.

## 🏗 Architecture

The system consists of 3 microservices running on Docker:

1.  **Backend (FastAPI):** Orchestrator that collects telemetry and talks to io Intelligence API.
2.  **Frontend (Streamlit):** Dashboard for monitoring and control.
3.  **Workers (Python):** Simulates GPU nodes and telemetry.

## 🚀 Getting Started

### Prerequisites

*   Docker & Docker Compose
*   io.net API Key (for io Intelligence)

### Installation

1.  **Configure Environment:**
    Open `.env` file and set your `IO_API_KEY`.
    ```bash
    IO_API_KEY="sk-io-................"
    ```

2.  **Run with Docker Compose:**
    ```bash
    docker-compose up --build
    ```

3.  **Access Dashboard:**
    Open [http://localhost:8501](http://localhost:8501) in your browser.

## 🧪 Simulation Guide

*   **Normal Operation:** 3 Workers send telemetry every ~0.1s.
*   **Chaos Mode:** Worker 3 has `CHAOS_MODE` configurable in `docker-compose.yml`. Set it to `True` (or modify `worker.py`) to simulate a straggler (latency > 2s).
*   **AI Analysis:** Click "Scan for Stragglers" on the dashboard to let AI detect and kill the straggler.

## 📁 Project Structure

```text
io-guard/
├── .env                        # API Key
├── docker-compose.yml          # Service definition
├── backend/                    # FastAPI
├── frontend/                   # Streamlit
└── workers/                    # Simulation scripts
```

---
*Built for io.net Hackathon MVP*
