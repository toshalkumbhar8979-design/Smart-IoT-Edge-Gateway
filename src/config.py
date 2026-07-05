"""
Central configuration for the Smart IoT Edge Gateway Platform.
Keeping all tunables here means every component (sensors, gateway, cloud)
reads from a single source of truth.
"""

# --- MQTT Broker ---
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
MQTT_KEEPALIVE = 60

# --- Topics ---
# Sensors publish to "iot/sensors/<sensor_id>/<metric>"
TOPIC_WILDCARD = "iot/sensors/#"

def sensor_topic(sensor_id: str, metric: str) -> str:
    return f"iot/sensors/{sensor_id}/{metric}"

# --- Simulated Sensor Fleet ---
SENSOR_IDS = ["node-01", "node-02", "node-03"]
METRICS = ["temperature", "humidity", "motion"]

# Normal operating ranges per metric (used to generate realistic readings)
METRIC_RANGES = {
    "temperature": {"min": 18.0, "max": 26.0, "unit": "C"},
    "humidity": {"min": 30.0, "max": 60.0, "unit": "%"},
    "motion": {"min": 0, "max": 1, "unit": "bool"},  # 0 = no motion, 1 = motion
}

PUBLISH_INTERVAL_SEC = 2          # how often each sensor publishes
ANOMALY_INJECTION_PROBABILITY = 0.05  # 5% chance a reading is an injected anomaly

# --- Edge Gateway ---
ROLLING_WINDOW_SIZE = 20          # number of readings kept per sensor/metric for stats
ZSCORE_ANOMALY_THRESHOLD = 2.5    # readings beyond this many std-devs are flagged
SUMMARY_FORWARD_INTERVAL_SEC = 10 # how often aggregated summaries are pushed to cloud
LOCAL_DB_PATH = "edge_data.db"

# --- Cloud Server ---
CLOUD_SERVER_HOST = "0.0.0.0"
CLOUD_SERVER_PORT = 5000
CLOUD_INGEST_ENDPOINT = f"http://localhost:{CLOUD_SERVER_PORT}/api/ingest"
CLOUD_ANOMALY_ENDPOINT = f"http://localhost:{CLOUD_SERVER_PORT}/api/anomaly"
CLOUD_DB_PATH = "cloud_data.db"
