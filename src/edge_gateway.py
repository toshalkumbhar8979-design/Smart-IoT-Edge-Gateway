"""
edge_gateway.py
---------------
The heart of the "edge computing" pattern in this project.

Responsibilities:
1. Subscribe to all raw sensor telemetry over MQTT.
2. Maintain a rolling window (per sensor+metric) and compute live stats.
3. Detect anomalies locally using z-score deviation from the rolling mean.
4. Persist every raw reading to a local SQLite DB (edge-side audit log).
5. Periodically forward *aggregated summaries* (not raw data) to the cloud,
   and immediately forward any detected anomaly as a separate event.

This is what makes it "edge" computing: the gateway does the heavy lifting
close to the data source, only sending the cloud what it actually needs.
"""

import json
import sqlite3
import threading
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
import requests

import config
from analytics import RollingStats

# sensor_id::metric -> RollingStats
stats_table: dict[str, RollingStats] = {}
stats_lock = threading.Lock()


def get_stats(sensor_id: str, metric: str) -> RollingStats:
    key = f"{sensor_id}::{metric}"
    if key not in stats_table:
        stats_table[key] = RollingStats(window_size=config.ROLLING_WINDOW_SIZE)
    return stats_table[key]


def init_db():
    conn = sqlite3.connect(config.LOCAL_DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT, metric TEXT, value REAL,
            timestamp TEXT, is_anomaly INTEGER
        )"""
    )
    conn.commit()
    return conn


def on_connect(client, userdata, flags, rc, properties=None):
    print(f"[edge-gateway] connected to broker (rc={rc}), subscribing to {config.TOPIC_WILDCARD}")
    client.subscribe(config.TOPIC_WILDCARD)


def on_message(client, userdata, msg):
    conn: sqlite3.Connection = userdata["conn"]
    try:
        payload = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        print(f"[edge-gateway] dropped malformed message on {msg.topic}")
        return

    sensor_id = payload["sensor_id"]
    metric = payload["metric"]
    value = payload["value"]

    with stats_lock:
        stats = get_stats(sensor_id, metric)
        anomaly = stats.is_anomaly(value, config.ZSCORE_ANOMALY_THRESHOLD)
        stats.add(value)

    conn.execute(
        "INSERT INTO readings (sensor_id, metric, value, timestamp, is_anomaly) VALUES (?, ?, ?, ?, ?)",
        (sensor_id, metric, value, payload["timestamp"], int(anomaly)),
    )
    conn.commit()

    if anomaly:
        print(f"[edge-gateway] ANOMALY detected: {sensor_id}/{metric}={value}")
        forward_anomaly(sensor_id, metric, value, payload["timestamp"])


def forward_anomaly(sensor_id: str, metric: str, value: float, timestamp: str):
    try:
        requests.post(
            config.CLOUD_ANOMALY_ENDPOINT,
            json={"sensor_id": sensor_id, "metric": metric, "value": value, "timestamp": timestamp},
            timeout=3,
        )
    except requests.RequestException as e:
        print(f"[edge-gateway] failed to forward anomaly to cloud: {e}")


def forward_summaries_loop():
    """Periodically push aggregated (not raw) stats to the cloud server."""
    while True:
        time.sleep(config.SUMMARY_FORWARD_INTERVAL_SEC)
        with stats_lock:
            snapshot = {key: s.summary() for key, s in stats_table.items()}

        for key, summary in snapshot.items():
            sensor_id, metric = key.split("::")
            body = {
                "sensor_id": sensor_id,
                "metric": metric,
                "summary": summary,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            try:
                requests.post(config.CLOUD_INGEST_ENDPOINT, json=body, timeout=3)
            except requests.RequestException as e:
                print(f"[edge-gateway] failed to forward summary for {key}: {e}")

        if snapshot:
            print(f"[edge-gateway] forwarded {len(snapshot)} summaries to cloud")


def main():
    conn = init_db()
    client = mqtt.Client(client_id="edge-gateway", userdata={"conn": conn}, protocol=mqtt.MQTTv311)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(config.MQTT_BROKER_HOST, config.MQTT_BROKER_PORT, config.MQTT_KEEPALIVE)

    threading.Thread(target=forward_summaries_loop, daemon=True).start()

    print("Edge gateway running. Press Ctrl+C to stop.")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nStopping edge gateway.")
        conn.close()


if __name__ == "__main__":
    main()
