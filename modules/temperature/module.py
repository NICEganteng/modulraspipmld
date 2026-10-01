import json
import time

import paho.mqtt.client as mqtt


DEVICE = json.load(open("/opt/iot-agent/device.json"))
DEVICE_ID = DEVICE["device_id"]
ROOM_ID = DEVICE.get("room_id", "unknown")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

client.connect(
    DEVICE["mqtt_host"],
    DEVICE["mqtt_port"],
    60,
)

client.loop_start()


def read_temp():
    """Membaca suhu CPU dan mengonversinya ke Fahrenheit."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            celsius = int(f.read().strip()) / 1000.0
            fahrenheit = (celsius * 1.8) + 32
            return round(fahrenheit, 2)
    except Exception:
        return 0.0



while True:
    payload = {
        "device_id": DEVICE_ID,
        "room_id": ROOM_ID,
        "temperature": read_temp(),
        "ts": time.time(),
    }

    client.publish(
        f"iot/room/{ROOM_ID}/temperature",
        json.dumps(payload),
        qos=1,
    )

    time.sleep(10)
