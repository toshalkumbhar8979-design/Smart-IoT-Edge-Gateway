"""
sensor_node.py
--------------
Simulates a fleet of independent IoT sensor nodes. Each node runs on its own
thread and periodically publishes telemetry (temperature, humidity, motion)
to the MQTT broker, exactly as a real embedded device would.

Realism features:
- Gaussian noise around a normal baseline (sensors are never perfectly stable)
- Occasional injected anomalies (simulates faults / real-world events)
- Independent publish timing per node (jitter) to avoid synchronized bursts
"""

import json
import random
import threading
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

import config


def generate_reading(metric: str) -> float:
    """Generate a realistic reading for a given metric, with occasional anomalies."""
    bounds = config.METRIC_RANGES[metric]

    if metric == "motion":
        return 1 if random.random() < 0.1 else 0

    baseline = random.uniform(bounds["min"], bounds["max"])
    noise = random.gauss(0, 0.4)
    value = baseline + noise

    # Occasionally inject a clear anomaly (spike or drop)
    if random.random() < config.ANOMALY_INJECTION_PROBABILITY:
        spike_direction = random.choice([1, -1])
        value += spike_direction * random.uniform(8, 15)

    return round(value, 2)


def sensor_loop(sensor_id: str, client: mqtt.Client):
    """Continuously publish readings for one sensor node."""
    while True:
        for metric in config.METRICS:
            value = generate_reading(metric)
            payload = {
                "sensor_id": sensor_id,
                "metric": metric,
                "value": value,
                "unit": config.METRIC_RANGES[metric]["unit"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            topic = config.sensor_topic(sensor_id, metric)
            client.publish(topic, json.dumps(payload))
            print(f"[{sensor_id}] published {metric}={value} -> {topic}")

        # small per-node jitter so nodes don't all publish in lockstep
        time.sleep(config.PUBLISH_INTERVAL_SEC + random.uniform(-0.3, 0.3))


def main():
    client = mqtt.Client(client_id="sensor-simulator", protocol=mqtt.MQTTv311)
    client.connect(config.MQTT_BROKER_HOST, config.MQTT_BROKER_PORT, config.MQTT_KEEPALIVE)
    client.loop_start()

    threads = []
    for sensor_id in config.SENSOR_IDS:
        t = threading.Thread(target=sensor_loop, args=(sensor_id, client), daemon=True)
        t.start()
        threads.append(t)

    print(f"Simulating {len(config.SENSOR_IDS)} sensor nodes. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping sensor simulation.")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
