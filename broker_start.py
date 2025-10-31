import argparse
import os
import socket
import subprocess
import sys
import time

# --- EDIT THESE IF NEEDED ---
MOSQUITTO_EXE = r"C:\Program Files\mosquitto\mosquitto.exe"
CONF_PATH     = r"C:\Users\Renz\CODES\FLAME-DETECTOR\mosquitto\mosquitto.conf"

BROKER_HOST   = "192.168.68.110"      # for local test; change to LAN IP to test from other devices
BROKER_PORT   = 1883
MQTT_USER     = "iotuser"
MQTT_PASS     = "emtech_broker"   # <-- put the one you set

def wait_for_port(host: str, port: int, timeout: float = 10.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            try:
                s.connect((host, port))
                return True
            except OSError:
                time.sleep(0.2)
    return False

def run_broker(verbose: bool = True):
    if not os.path.isfile(MOSQUITTO_EXE):
        print(f"[ERR] mosquitto.exe not found at: {MOSQUITTO_EXE}")
        sys.exit(1)
    if not os.path.isfile(CONF_PATH):
        print(f"[ERR] mosquitto.conf not found at: {CONF_PATH}")
        sys.exit(1)

    args = [MOSQUITTO_EXE, "-v", "-c", CONF_PATH]

    # Start mosquitto and stream its output
    print("[INFO] Starting Mosquitto…")
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    # Wait a bit for startup and show initial logs
    start = time.time()
    while time.time() - start < 3:
        if proc.poll() is not None:
            print("[ERR] Mosquitto exited early.")
            break
        if proc.stdout and proc.stdout.readable():
            line = proc.stdout.readline()
            if not line:
                break
            if verbose:
                print(line.rstrip())

    # Wait for port to be ready
    if wait_for_port(BROKER_HOST, BROKER_PORT, timeout=10):
        print(f"[OK] Broker listening on {BROKER_HOST}:{BROKER_PORT}")
        print("[INFO] Press Ctrl+C to stop. (Mosquitto will exit when you close this script)")
    else:
        print(f"[WARN] Could not confirm {BROKER_HOST}:{BROKER_PORT} is open. Check logs above.")

    try:
        # Keep streaming logs until Ctrl+C
        if proc.stdout:
            for line in proc.stdout:
                print(line.rstrip())
        proc.wait()
    except KeyboardInterrupt:
        print("\n[INFO] Stopping Mosquitto…")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("[INFO] Stopped.")

def test_pub_sub():
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        print("[ERR] paho-mqtt not installed. Run: pip install paho-mqtt")
        sys.exit(1)

    topic = "site/lab1/devices/esp32-01/in"
    payload = "{fire}{top-left}"
    got = {"msg": None}

    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("[OK] Connected, subscribing…")
            client.subscribe(topic, qos=1)
        else:
            print(f"[ERR] Connect failed rc={rc}")

    def on_message(client, userdata, msg):
        print(f"[MQTT] {msg.topic} -> {msg.payload.decode('utf-8', 'ignore')}")
        got["msg"] = msg.payload

    sub = mqtt.Client(client_id="test-sub")
    sub.username_pw_set(MQTT_USER, MQTT_PASS)
    sub.on_connect = on_connect
    sub.on_message = on_message
    sub.connect(BROKER_HOST, BROKER_PORT, keepalive=15)
    sub.loop_start()

    # give subscriber time to connect
    time.sleep(1.0)

    pub = mqtt.Client(client_id="test-pub")
    pub.username_pw_set(MQTT_USER, MQTT_PASS)
    pub.connect(BROKER_HOST, BROKER_PORT, keepalive=15)
    pub.loop_start()

    print(f"[INFO] Publishing test message to {topic}: {payload}")
    pub.publish(topic, payload, qos=1, retain=False)

    # wait for the echo
    for _ in range(30):
        if got["msg"] is not None:
            break
        time.sleep(0.2)

    sub.loop_stop()
    pub.loop_stop()
    sub.disconnect()
    pub.disconnect()

    if got["msg"] is None:
        print("[WARN] No message received. Is the broker running? Are creds correct?")
    else:
        print("[OK] Test successful.")

def main():
    ap = argparse.ArgumentParser(description="Mosquitto helper (Windows)")
    ap.add_argument("action", choices=["run","test"], nargs="?", default="run",
                help="'run' broker or 'test' pub/sub")
    args = ap.parse_args()

    if args.action == "run":
        run_broker()
    elif args.action == "test":
        test_pub_sub()

if __name__ == "__main__":
    main()
