# test_mqtt.py
import time
import argparse
from datetime import datetime

try:
    import paho.mqtt.client as mqtt
except ImportError:
    raise SystemExit("paho-mqtt not installed. Run: pip install paho-mqtt")

# --- Defaults (edit once, then forget) ---
MQTT_HOST = "192.168.68.110"     # your laptop's LAN IP
MQTT_PORT = 1883
MQTT_USER = "iotuser"
MQTT_PASS = "emtech_broker"      # your current password
TOPIC     = "site/lab1/devices/esp32-01/in"
CLIENT_ID = "sub-cli-esp32-01"

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"[OK] Connected to {userdata['host']}:{userdata['port']} as {CLIENT_ID}")
        client.subscribe(userdata["topic"], qos=1)
        print(f"[OK] Subscribed: {userdata['topic']}")
    else:
        print(f"[ERR] Connect failed rc={rc}")

def on_message(client, userdata, msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        payload = msg.payload.decode("utf-8", "ignore")
    except Exception:
        payload = str(msg.payload)
    print(f"[{ts}] {msg.topic} -> {payload}")

def main():
    ap = argparse.ArgumentParser(description="Simple MQTT subscriber")
    ap.add_argument("-H", "--host", default=MQTT_HOST)
    ap.add_argument("-p", "--port", type=int, default=MQTT_PORT)
    ap.add_argument("-u", "--user", default=MQTT_USER)
    ap.add_argument("-P", "--password", default=MQTT_PASS)
    ap.add_argument("-t", "--topic", default=TOPIC)
    args = ap.parse_args()

    userdata = {"host": args.host, "port": args.port, "topic": args.topic}

    client = mqtt.Client(client_id=CLIENT_ID, userdata=userdata)
    client.username_pw_set(args.user, args.password)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(args.host, args.port, keepalive=30)
        print("[INFO] Listening…  (Ctrl+C to stop)")
        client.loop_forever(retry_first_connection=True)
    except KeyboardInterrupt:
        print("\n[INFO] Stopping…")
    except Exception as e:
        print(f"[ERR] {e}")

if __name__ == "__main__":
    main()
