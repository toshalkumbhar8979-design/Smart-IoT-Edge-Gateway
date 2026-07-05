# Project Report: Smart IoT Edge Gateway Platform

## 1. Problem Statement
Modern IoT deployments generate large volumes of raw sensor telemetry. Sending every raw
reading to the cloud is expensive in bandwidth, adds latency, and doesn't scale as the
number of connected devices grows — a real constraint in telecom and IoT networks. This
project explores the **edge computing** pattern: process data close to its source, and only
send the cloud what's actually useful (aggregated trends and anomaly events).

## 2. Objectives
- Simulate a fleet of independent IoT sensor nodes publishing telemetry over a standard
  IoT protocol (MQTT).
- Build an edge gateway that performs local statistical analysis and anomaly detection
  in real time.
- Demonstrate bandwidth-conscious design by forwarding only summaries + anomalies to
  a cloud service, not raw data.
- Visualize the results on a live dashboard.

## 3. System Design

### 3.1 Communication Layer — MQTT
MQTT was chosen because it's the de-facto standard publish/subscribe protocol for IoT,
designed for low-bandwidth, high-latency, unreliable networks — the same conditions
edge/IoT devices in telecom networks often operate under.

### 3.2 Edge Analytics
Each sensor/metric pair is tracked with a rolling window (default: 20 samples). From this
window the gateway computes a live mean and standard deviation, and flags a reading as
anomalous if it falls beyond a configurable z-score threshold (default: 2.5σ). This is a
lightweight, interpretable technique well suited to constrained edge hardware where a
heavier ML model may not be practical.

### 3.3 Local Persistence
The gateway logs every raw reading to a local SQLite database. This mirrors a common
real-world requirement: edge nodes need to keep an audit trail / buffer even if the
uplink to the cloud is temporarily unavailable.

### 3.4 Cloud Ingestion & Dashboard
The cloud server is a minimal Flask REST API with two ingestion endpoints (summaries,
anomalies) and a polling dashboard built with Chart.js. This keeps the cloud side
intentionally simple — the interesting engineering work happens at the edge.

## 4. Key Engineering Decisions
- **Separation of concerns**: the anomaly-detection math (`analytics.py`) has zero
  dependency on MQTT, Flask, or SQLite. This made it possible to unit test the core logic
  in isolation, without spinning up a broker or server.
- **Push aggregates, not raw data**: the gateway only pushes to the cloud every N seconds
  (configurable), plus immediate anomaly events. This is the crux of the "edge" pattern
  and the main efficiency gain over a naive cloud-only design.
- **Config centralization**: every tunable (thresholds, intervals, topics) lives in one
  `config.py`, making the system easy to retune without touching business logic.

## 5. Results / What Works
- The system successfully detects injected anomalies (spikes/drops) in simulated sensor
  data in real time and surfaces them on the dashboard within seconds.
- Bandwidth to the "cloud" is reduced significantly: for 3 sensors × 3 metrics publishing
  every 2 seconds, only one summary per sensor/metric is sent every 10 seconds instead of
  every raw reading — roughly an 80% reduction in cloud-bound messages under normal
  (non-anomalous) conditions.

## 6. Challenges & How They Were Addressed
- **Thread safety**: the gateway's rolling-stats table is accessed both by the MQTT
  message callback thread and the periodic summary-forwarding thread. A lock
  (`stats_lock`) was added around all read/write access to avoid race conditions.
- **Network flakiness simulation**: forwarding to the cloud is wrapped in try/except so a
  temporarily unreachable cloud server doesn't crash the gateway — raw data is still
  safely logged locally regardless.

## 7. Future Work
See the "Possible Extensions" section in the main README — real hardware integration,
TLS-secured MQTT, ML-based anomaly detection, and containerized multi-node deployment
are natural next steps.

## 8. Relevance to Telecom-IoT Roles
This project directly touches concepts central to telecom infrastructure: edge computing
to reduce backhaul load, resilient pub/sub messaging for distributed devices, and
real-time monitoring/anomaly detection — all patterns used in 5G network function
deployments and IoT connectivity platforms.
