"""
cloud_server.py
----------------
Simulates the "cloud" side of the platform: a lightweight Flask REST API that
receives aggregated summaries and anomaly events from the edge gateway,
persists them, and serves a live dashboard.

Endpoints:
  POST /api/ingest   - receive an aggregated summary from the edge gateway
  POST /api/anomaly  - receive an anomaly event from the edge gateway
  GET  /api/data      - return recent summaries + anomalies (used by dashboard JS)
  GET  /              - dashboard UI
"""

import sqlite3
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request

import config

app = Flask(__name__, template_folder="../dashboard/templates", static_folder="../dashboard/static")


def get_db():
    conn = sqlite3.connect(config.CLOUD_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT, metric TEXT,
            mean REAL, stdev REAL, min REAL, max REAL, count INTEGER,
            timestamp TEXT
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT, metric TEXT, value REAL, timestamp TEXT
        )"""
    )
    conn.commit()
    conn.close()


@app.route("/api/ingest", methods=["POST"])
def ingest():
    body = request.get_json(force=True)
    summary = body["summary"]
    conn = get_db()
    conn.execute(
        """INSERT INTO summaries (sensor_id, metric, mean, stdev, min, max, count, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            body["sensor_id"], body["metric"],
            summary["mean"], summary["stdev"], summary["min"], summary["max"], summary["count"],
            body["timestamp"],
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"}), 201


@app.route("/api/anomaly", methods=["POST"])
def anomaly():
    body = request.get_json(force=True)
    conn = get_db()
    conn.execute(
        "INSERT INTO anomalies (sensor_id, metric, value, timestamp) VALUES (?, ?, ?, ?)",
        (body["sensor_id"], body["metric"], body["value"], body["timestamp"]),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"}), 201


@app.route("/api/data")
def data():
    conn = get_db()
    summaries = conn.execute(
        "SELECT * FROM summaries ORDER BY id DESC LIMIT 100"
    ).fetchall()
    anomalies = conn.execute(
        "SELECT * FROM anomalies ORDER BY id DESC LIMIT 20"
    ).fetchall()
    conn.close()
    return jsonify({
        "summaries": [dict(row) for row in summaries],
        "anomalies": [dict(row) for row in anomalies],
        "server_time": datetime.now(timezone.utc).isoformat(),
    })


@app.route("/")
def dashboard():
    return render_template("index.html")


if __name__ == "__main__":
    init_db()
    app.run(host=config.CLOUD_SERVER_HOST, port=config.CLOUD_SERVER_PORT, debug=True)
