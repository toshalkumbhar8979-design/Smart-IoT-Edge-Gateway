# Smart IoT Edge Gateway Platform

A simulated IoT sensor network with an MQTT-based **edge gateway** that performs local analytics
(rolling aggregation + anomaly detection) before forwarding condensed data to a cloud dashboard.

This project models a real-world pattern used in telecom/IoT infrastructure: pushing
compute to the edge to reduce bandwidth, latency, and cloud cost — directly relevant to
edge computing, 5G/IoT connectivity, and network operations work.

---

## Architecture

```
 ┌───────────────┐      MQTT       ┌──────────────────┐      REST/HTTP     ┌─────────────────┐
 │  Sensor Nodes │ ───────────────▶│   Edge Gateway    │───────────────────▶│  Cloud Server /  │
 │ (simulated)   │  publish raw    │ - buffers readings│  forward only      │  Dashboard       │
 │ temp/humidity │  telemetry      │ - rolling average │  aggregated +      │ - REST API       │
 │ /motion       │                 │ - anomaly detect  │  anomaly events    │ - SQLite storage │
 └───────────────┘                 │ - local SQLite log│                    │ - live charts     │
                                    └──────────────────┘                    └─────────────────┘
```

**Why this design?** Raw sensor data is noisy and high-volume. The gateway node (which in a
real deployment would sit physically close to the sensors, e.g. on a base station or local
hub) filters, aggregates, and only escalates *meaningful* events — anomalies and periodic
summaries — to the cloud. This mirrors how edge computing reduces backhaul traffic in real
IoT/telecom networks.

---

## Components

| File | Responsibility |
|---|---|
| `src/sensor_node.py` | Simulates N independent IoT sensor nodes publishing telemetry over MQTT at randomized intervals, with injected noise and occasional anomalies |
| `src/edge_gateway.py` | Subscribes to sensor topics, maintains a rolling window per sensor, computes moving average/std-dev, flags anomalies (z-score based), persists raw+aggregated data locally (SQLite), and forwards summaries to the cloud server via REST |
| `src/cloud_server.py` | Flask REST API that receives aggregated data & anomaly alerts, stores history, and serves a live dashboard |
| `dashboard/templates/index.html` | Live-updating dashboard (Chart.js) showing per-sensor trends and anomaly log |
| `src/config.py` | Central configuration (topics, thresholds, intervals) |
| `tests/test_edge_gateway.py` | Unit tests for the anomaly detection & aggregation logic |

---

## Setup

### 1. Install an MQTT broker (Mosquitto)
```bash
# Ubuntu/Debian
sudo apt-get install mosquitto mosquitto-clients
sudo systemctl start mosquitto

# macOS
brew install mosquitto
brew services start mosquitto
```

### 2. Install Python dependencies
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the system (3 terminals)
```bash
# Terminal 1 - Cloud server + dashboard
python src/cloud_server.py

# Terminal 2 - Edge gateway
python src/edge_gateway.py

# Terminal 3 - Sensor simulators
python src/sensor_node.py
```

### 4. Dashboard
<img width="1246" height="599" alt="image" src="https://github.com/user-attachments/assets/24033426-0d53-44a8-a0fa-c3058a2f83ff" />



---

## Running Tests
```bash
pytest tests/ -v
```

---

## What This Demonstrates (for interviews)

- **Distributed systems basics**: decoupled producers (sensors) and consumers (gateway) via a pub/sub broker
- **Edge computing pattern**: local processing before cloud escalation — bandwidth/latency aware design
- **Signal processing**: rolling statistics, z-score anomaly detection
- **Systems integration**: MQTT + REST + SQLite + a live web dashboard working together
- **Testable design**: core logic (anomaly detection, aggregation) is isolated and unit-tested independent of the network layer

## Possible Extensions (mention these in an interview to show forward thinking)
- Swap the simulated sensors for real hardware (Raspberry Pi + DHT22 sensor, ESP32 over Wi-Fi/MQTT)
- Add TLS + client-cert auth on MQTT for a security-hardened version
- Replace z-score detection with a lightweight ML model (e.g., isolation forest) for anomaly detection
- Containerize each component (Docker Compose) to simulate multi-node deployment
- Add horizontal scaling: multiple gateways behind a load-balanced cloud ingestion API

---

## Project Report
See [`docs/report.md`](docs/report.md) for a full write-up (problem statement, design decisions,
challenges, and results) suitable for a portfolio or university submission.
