"""
app.py
------
Single Flask app combining:
  1. MQTT listener (runs in a background thread)
  2. ML prediction on every incoming reading
  3. In-memory history (last 100 readings) + a /api/latest endpoint
  4. The dashboard HTML page itself

Deploy this on Render (or Railway) and you get ONE permanent URL.
No laptop, no Colab, no local server needed once deployed.
"""

import os
import json
import threading
import csv
import io
from datetime import datetime
from collections import deque

import joblib
import pandas as pd
import paho.mqtt.client as mqtt
from flask import Flask, jsonify, render_template, Response

app = Flask(__name__)

# ---------- Config ----------
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "transformer/T1/dga"
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
MAX_HISTORY = 100

ALERT_MAP = {
    "Normal": "SAFE",
    "Partial_Discharge": "WARNING",
    "Thermal_Fault": "CRITICAL",
    "Arcing": "CRITICAL",
}
RISK_MAP = {
    "Normal": "Low Risk",
    "Partial_Discharge": "Moderate Risk",
    "Thermal_Fault": "High Risk",
    "Arcing": "Severe Risk",
}

EXPLANATION_MAP = {
    "Normal": "Gas levels are within safe limits. The transformer is operating normally. No action needed.",
    "Partial_Discharge": "Small electrical discharges are occurring inside the insulation, often due to voids, "
                          "moisture, or contamination. Not immediately dangerous but should be monitored closely — "
                          "left unchecked, it can develop into more serious insulation damage over time.",
    "Thermal_Fault": "Abnormal heating is occurring inside the transformer, likely due to overloading, poor "
                      "connections, or core/winding issues. Continued operation at high temperature accelerates "
                      "insulation aging and can lead to failure. Inspection recommended soon.",
    "Arcing": "High-energy electrical arcing detected — a serious fault, often from severe insulation breakdown "
              "or a short circuit. This is the most dangerous condition and risks immediate transformer failure. "
              "Immediate inspection and possible shutdown is recommended.",
}

# ---------- Load model once at startup ----------
model = joblib.load(os.path.join(MODEL_DIR, "best_model.pkl"))
scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
le = joblib.load(os.path.join(MODEL_DIR, "label_encoder.pkl"))
feature_cols = joblib.load(os.path.join(MODEL_DIR, "feature_cols.pkl"))

# ---------- In-memory history (thread-safe via lock) ----------
history = deque(maxlen=MAX_HISTORY)
history_lock = threading.Lock()
last_reading_time = None


def predict(raw):
    h2 = raw.get("H2", 0.01) or 0.01
    c2h6 = raw.get("C2H6", 0.01) or 0.01
    c2h4 = raw.get("C2H4", 0.01) or 0.01
    row = {
        "H2": raw.get("H2", 0), "CH4": raw.get("CH4", 0),
        "C2H6": raw.get("C2H6", 0), "C2H4": raw.get("C2H4", 0),
        "C2H2": raw.get("C2H2", 0), "CO": raw.get("CO", 0), "CO2": raw.get("CO2", 0),
        "Ratio_CH4_H2": raw.get("CH4", 0) / h2,
        "Ratio_C2H4_C2H6": raw.get("C2H4", 0) / c2h6,
        "Ratio_C2H2_C2H4": raw.get("C2H2", 0) / c2h4,
    }
    df_in = pd.DataFrame([row])[feature_cols]
    scaled = scaler.transform(df_in)
    idx = model.predict(scaled)[0]
    prob = model.predict_proba(scaled)[0].max()
    return le.classes_[idx], float(prob)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[mqtt] Connected to broker.")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"[mqtt] Connection failed, code {rc}")


def on_message(client, userdata, msg):
    global last_reading_time
    try:
        raw = json.loads(msg.payload.decode())
        fault, conf = predict(raw)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Avoid duplicate readings landing within the same second
        if last_reading_time == ts:
            return
        last_reading_time = ts

        record = {
            "Timestamp": ts,
            "H2": raw.get("H2", 0), "CH4": raw.get("CH4", 0),
            "C2H6": raw.get("C2H6", 0), "C2H4": raw.get("C2H4", 0),
            "C2H2": raw.get("C2H2", 0), "CO": raw.get("CO", 0),
            "CO2": raw.get("CO2", 0),
            "Fault_Type": fault,
            "Confidence": round(conf, 4),
            "Alert": ALERT_MAP.get(fault, "UNKNOWN"),
            "Risk_Level": RISK_MAP.get(fault, "Unknown"),
            "Explanation": EXPLANATION_MAP.get(fault, "No explanation available."),
        }
        with history_lock:
            history.append(record)
        print(f"[mqtt] {ts} | {fault} | {ALERT_MAP.get(fault)} | conf={conf:.2f}")
    except Exception as e:
        print(f"[mqtt] Error processing message: {e}")


def start_mqtt_thread():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="render-transformer-listener")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()


# Start MQTT listener in a background thread when the app boots
mqtt_thread = threading.Thread(target=start_mqtt_thread, daemon=True)
mqtt_thread.start()


# ---------- Routes ----------

@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/latest")
def api_latest():
    with history_lock:
        rows = list(history)
    if not rows:
        return jsonify({"status": "waiting", "latest": None, "history": []})
    return jsonify({
        "status": "live",
        "latest": rows[-1],
        "history": rows[-15:],
        "total_readings": len(rows),
    })


@app.route("/api/download_csv")
def download_csv():
    with history_lock:
        rows = list(history)
    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=transformer_log.csv"},
    )


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
