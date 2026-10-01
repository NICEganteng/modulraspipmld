import json
import time
from pathlib import Path
import paho.mqtt.client as mqtt

DEVICE_CONFIG = Path("/opt/iot-agent/device.json")
DEVICE = json.load(DEVICE_CONFIG.open())
DEVICE_ID = DEVICE["device_id"]
ROOM_ID = DEVICE.get("room_id", "unknown")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(DEVICE["mqtt_host"], DEVICE["mqtt_port"], 60)
client.loop_start()

def get_ram_usage():
    """Membaca persentase penggunaan RAM dari /proc/meminfo bawaan Linux."""
    try:
        meminfo = {}
        with open("/proc/meminfo") as f:
            for line in f:
                parts = line.split(":")
                meminfo[parts[0].strip()] = int(parts[1].split()[0])
        total = meminfo.get("MemTotal", 1)
        available = meminfo.get("MemAvailable", 0)
        used = total - available
        return round((used / total) * 100, 2)
    except Exception:
        return 0.0

print(f"[Memory Module] Dimulai untuk device {DEVICE_ID} di ruangan {ROOM_ID}")

while True:
    payload = {
        "device_id": DEVICE_ID,
        "room_id": ROOM_ID,
        "ram_usage_percent": get_ram_usage(),
        "ts": time.time(),
    }

    topic = f"iot/room/{ROOM_ID}/memory"
    client.publish(topic, json.dumps(payload), qos=0)
    time.sleep(15)
