import json
import socket
import threading
import time
from pathlib import Path

import paho.mqtt.client as mqtt

from module_manager import reconcile


DEVICE = json.load(
    open("/opt/iot-agent/device.json")
)

DEVICE_ID = DEVICE["device_id"]

DESIRED = Path(
    "/opt/iot-agent/desired.json"
)

LOCK = threading.Lock()


client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2
)


def report(
    module,
    version,
    status,
    detail="",
):
    payload = {
        "device_id": DEVICE_ID,
        "module": module,
        "version": version,
        "status": status,
        "detail": detail,
        "ts": time.time(),
    }

    client.publish(
        f"iot/device/{DEVICE_ID}/deployment",
        json.dumps(payload),
        qos=1,
    )


def apply(desired):
    with LOCK:
        reconcile(
            desired,
            report,
        )


def on_connect(
    client,
    userdata,
    flags,
    reason_code,
    properties,
):
    client.subscribe(
        f"iot/device/{DEVICE_ID}/config",
        qos=1,
    )

    client.publish(
        f"iot/device/{DEVICE_ID}/register",
        json.dumps(
            {
                "device_id": DEVICE_ID,
                "hostname": socket.gethostname(),
                "agent_version": "0.1.0",
            }
        ),
        qos=1,
    )


def on_message(
    client,
    userdata,
    msg,
):
    desired = json.loads(
        msg.payload
    )

    DESIRED.write_text(
        json.dumps(
            desired,
            indent=2,
        )
    )

    threading.Thread(
        target=apply,
        args=(desired,),
        daemon=True,
    ).start()


client.on_connect = on_connect
client.on_message = on_message


client.connect(
    DEVICE["mqtt_host"],
    DEVICE["mqtt_port"],
    60,
)


# Apply cached desired state if VPS is unavailable
if DESIRED.exists():
    threading.Thread(
        target=apply,
        args=(
            json.loads(
                DESIRED.read_text()
            ),
        ),
        daemon=True,
    ).start()


client.loop_forever()
