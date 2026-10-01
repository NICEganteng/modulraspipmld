#!/usr/bin/env bash

set -euo pipefail


MQTT_HOST="${MQTT_HOST:?MQTT_HOST is required}"
ROOM_ID="${ROOM_ID:?ROOM_ID is required}"
REPO_URL="${REPO_URL:?REPO_URL is required}"


apt-get update
apt-get install -y \
    git \
    python3 \
    python3-venv


# Clone repository dengan Sparse-Checkout (Tanpa mengunduh modul apapun diawal)
if [ ! -d /opt/iot-platform ]; then
    git clone --filter=blob:none --no-checkout "$REPO_URL" /opt/iot-platform
    git -C /opt/iot-platform sparse-checkout init --cone
    # Hanya checkout folder agent, scripts, dan systemd
    git -C /opt/iot-platform sparse-checkout set agent scripts systemd
    git -C /opt/iot-platform checkout main
else
    git -C /opt/iot-platform pull --ff-only
fi

# Prepare directories
mkdir -p \
    /opt/iot-agent \
    /opt/iot/modules


# Generate device identity once
if [ ! -f /opt/iot-agent/device.json ]; then

    DEVICE_ID="raspi-$(cut -c1-6 /etc/machine-id)"

    cat > /opt/iot-agent/device.json <<EOF_DEVICE
{
    "device_id": "$DEVICE_ID",
    "room_id": "$ROOM_ID",
    "mqtt_host": "$MQTT_HOST",
    "mqtt_port": 1883
}
EOF_DEVICE

fi


# Agent virtual environment
python3 -m venv \
    /opt/iot-agent/venv


/opt/iot-agent/venv/bin/pip install \
    -r /opt/iot-platform/agent/requirements.txt


# Install systemd units
cp \
    /opt/iot-platform/systemd/iot-agent.service \
    /etc/systemd/system/


cp \
    /opt/iot-platform/systemd/iot-module@.service \
    /etc/systemd/system/


systemctl daemon-reload


systemctl enable --now \
    iot-agent


echo
echo "======================================"
echo "IoT Agent installation completed"
echo "======================================"
echo "Device ID:"
cat /opt/iot-agent/device.json
