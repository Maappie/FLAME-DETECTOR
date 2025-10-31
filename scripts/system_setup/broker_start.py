# C:\Users\Renz\CODES\FLAME-DETECTOR\scripts\system_setup\broker_start.py
import argparse
import os
import socket
import subprocess
import sys
import time

from scripts.flame_detection.config import MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASS  

MOSQUITTO_EXE = r"C:\Program Files\mosquitto\mosquitto.exe"
CONF_PATH     = r"C:\Users\Renz\CODES\FLAME-DETECTOR\mosquitto\mosquitto.conf"

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
    print("[INFO] Starting Mosquitto…")
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

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

    if wait_for_port(MQTT_HOST, MQTT_PORT, timeout=10):
        print(f"[OK] Broker listening on {MQTT_HOST}:{MQTT_PORT}")
        print("[INFO] Press Ctrl+C to stop. (Mosquitto will exit when you close this script)")
    else:
        print(f"[WARN] Could not confirm {MQTT_HOST}:{MQTT_PORT} is open. Check logs above.")

    try:
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

def main():
    ap = argparse.ArgumentParser(description="Mosquitto helper (Windows)")
    ap.add_argument("action", choices=["run"], nargs="?", default="run")
    args = ap.parse_args()
    run_broker()

if __name__ == "__main__":
    main()
