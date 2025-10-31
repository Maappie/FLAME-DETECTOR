"""
stream.py — MJPEG server that subscribes to frames from main.py via ZeroMQ.

Run order:
  1) python main.py     (produces frames + MQTT)
  2) python stream.py   (serves MJPEG from those frames)

Open:
  http://127.0.0.1:5001/stream.mjpg?token=dev-secret-123
  (or from LAN: http://<your-ip>:5001/stream.mjpg?token=...)
"""

import os
import time
import threading
from collections import deque
from flask import Flask, Response, request, abort
import zmq

# -----------------------
# Server settings
# -----------------------
BIND_HOST   = os.getenv("BIND_HOST", "0.0.0.0")
BIND_PORT   = int(os.getenv("BIND_PORT", "5001"))
STREAM_PATH = os.getenv("STREAM_PATH", "/stream.mjpg")
ACCESS_TOKEN = os.getenv("STREAM_TOKEN", "dev-secret-123")
JPEG_QUALITY = int(os.getenv("JPEG_QUALITY", "80"))  # kept for symmetry; frames already JPEG

# ZeroMQ endpoint that main.py publishes to:
ZMQ_ENDPOINT = os.getenv("ZMQ_ENDPOINT", "tcp://127.0.0.1:5556")

# Frame buffer (keep only the latest 1–2 frames)
_buffer = deque(maxlen=2)

# -----------------------
# ZMQ subscriber thread
# -----------------------
def _subscriber():
    ctx = zmq.Context.instance()
    sub = ctx.socket(zmq.SUB)
    sub.connect(ZMQ_ENDPOINT)
    sub.setsockopt(zmq.SUBSCRIBE, b"")  # subscribe to all
    sub.setsockopt(zmq.RCVHWM, 4)
    while True:
        try:
            jpg = sub.recv()  # bytes
            _buffer.append(jpg)
        except Exception:
            time.sleep(0.01)

t = threading.Thread(target=_subscriber, daemon=True)
t.start()

# -----------------------
# Flask app
# -----------------------
app = Flask(__name__)

@app.get("/")
def health():
    return {
        "ok": True,
        "source": ZMQ_ENDPOINT,
        "path": STREAM_PATH,
        "requires_token": bool(ACCESS_TOKEN),
    }

def gen_mjpeg():
    # If we haven’t received anything yet, wait a little
    last = None
    idle_stamps = 0
    while True:
        if _buffer:
            last = _buffer[-1]
            idle_stamps = 0
        else:
            idle_stamps += 1
            time.sleep(0.02)
            continue

        # Serve the latest JPEG as an MJPEG part
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + last + b"\r\n")

@app.get(STREAM_PATH)
def stream():
    token = request.args.get("token", "")
    if ACCESS_TOKEN and token != ACCESS_TOKEN:
        abort(401)
    return Response(gen_mjpeg(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    print(f"[INFO] Subscribing to {ZMQ_ENDPOINT}")
    print(f"[INFO] Serving MJPEG at http://{BIND_HOST}:{BIND_PORT}{STREAM_PATH}?token=***")
    app.run(host=BIND_HOST, port=BIND_PORT, threaded=True)
