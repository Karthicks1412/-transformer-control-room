"""
simulate_esp32.py
------------------
Run this from YOUR LAPTOP (not on Render) to send test data to the
deployed app's MQTT broker, so you can verify the cloud dashboard
works correctly before real hardware is connected.

Once hardware exists, you simply stop running this and power on the
ESP32 instead — nothing on the server side changes.
"""

import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "transformer/T1/dga"

SCENARIOS = [
    {"H2": 20,  "CH4": 15,  "C2H6": 10,  "C2H4": 8,   "C2H2": 0.5, "CO": 300, "CO2": 3000, "name": "Normal"},
    {"H2": 22,  "CH4": 14,  "C2H6": 10,  "C2H4": 8,   "C2H2": 0.5, "CO": 310, "CO2": 2990, "name": "Normal"},
    {"H2": 150, "CH4": 40,  "C2H6": 10,  "C2H4": 9,   "C2H2": 1.2, "CO": 350, "CO2": 3200, "name": "Partial Discharge"},
    {"H2": 60,  "CH4": 180, "C2H6": 120, "C2H4": 250, "C2H2": 2.0, "CO": 500, "CO2": 4500, "name": "Thermal Fault"},
    {"H2": 300, "CH4": 150, "C2H6": 40,  "C2H4": 200, "C2H2": 180, "CO": 450, "CO2": 4000, "name": "Arcing"},
    {"H2": 18,  "CH4": 16,  "C2H6": 10,  "C2H4": 8,   "C2H2": 0.5, "CO": 295, "CO2": 3010, "name": "Normal"},
]


def jitter(v, p=0.05):
    return max(0.0, round(v * (1 + (random.random() * 2 - 1) * p), 1))


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[simulator] Connected to MQTT broker.")


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="ESP32-Sim-Test")
    client.on_connect = on_connect
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    time.sleep(2)

    idx = 0
    print("[simulator] Sending 1 test reading every 30 seconds. Ctrl+C to stop.")
    print("[simulator] Open your Render dashboard URL in a browser to watch it update.")
    while True:
        base = SCENARIOS[idx % len(SCENARIOS)]
        payload = {
            "transformer_id": "T1",
            "H2": jitter(base["H2"]), "CH4": jitter(base["CH4"]),
            "C2H6": jitter(base["C2H6"]), "C2H4": jitter(base["C2H4"]),
            "C2H2": jitter(base["C2H2"]), "CO": jitter(base["CO"]),
            "CO2": jitter(base["CO2"]),
        }
        client.publish(MQTT_TOPIC, json.dumps(payload))
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[simulator][{ts}] Sent: {base['name']}")
        idx += 1
        time.sleep(30)


if __name__ == "__main__":
    main()
