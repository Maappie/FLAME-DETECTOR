import os
from datetime import datetime
import cv2

# --- CONFIG ---
MODEL_PATH = r"C:\Users\Renz\CODES\FLAME-DETECTOR\-FLAME_DETECTOR\best.pt"
CONF_THRESH = 0.3
FIRE_LABELS = {"fire", "flame", "flames"}  # change to your exact class name(s)

# Camera (Windows example)
CAMERA_SOURCE = 0               # or 'video=Iriun Webcam'
CAP_BACKEND   = cv2.CAP_DSHOW   # Windows DirectShow. macOS: CAP_AVFOUNDATION, Linux: CAP_V4L2

# Optional: ask the camera for this size (driver may ignore)
# DESIRED_W, DESIRED_H = 720, 1280  # portrait request (try 1080x1920 if you want)

# Video save toggle
SAVE_VIDEO = False
SAVE_DIR = r"C:\Users\Renz\CODES\FLAME-DETECTOR\runs\videos"
os.makedirs(SAVE_DIR, exist_ok=True)
VIDEO_FILENAME = os.path.join(
    SAVE_DIR, f"annotated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
)
VIDEO_FPS_FALLBACK = 30.0  # used only if camera FPS is unknown

# --- GRID CONFIG (fixed 2x2) ---
GRID_ROWS = 2
GRID_COLS = 2
LINE_THICKNESS = 1
LINE_COLOR = (0, 0, 255)   # BGR (yellow)

SHOW_NUMBERS_DEFAULT = True
NUM_COLOR = (255, 255, 255)  # text color
NUM_BG = (0, 0, 0)           # background box
NUM_THICKNESS = 2

# --- ORIENTATION ---
FORCE_PORTRAIT = True          # set False to keep native landscape
# Options: 'cw' (90° clockwise), 'ccw' (90° counter-clockwise), '180'
ROTATE_DIRECTION = 'cw'

# ---------------- MQTT (ESP32 now, Rails later) ----------------
# Enable/disable independent publishers
MQTT_ENABLE_ESP32 = True
MQTT_ENABLE_RAILS = True  # keep False for now; flip to True when ready

# Broker settings (point ESP32 + Rails to the same broker)
MQTT_HOST = "192.168.68.121"   # your laptop LAN IP
MQTT_PORT = 1883
MQTT_KEEPALIVE = 30
MQTT_USER = "iotuser"
MQTT_PASS = "emtech_broker"    # <-- EXACTLY as in pwfile

# Topics
TOPIC_ESP32 = "site/lab1/devices/esp32-01/in"   # ESP32 subscribes here
TOPIC_RAILS = "site/lab1/ingest/rails"          # Rails worker subscribes here (later)

# Client IDs
CLIENT_ID_ESP32 = "yolo-pub-esp32"
CLIENT_ID_RAILS = "yolo-pub-rails"
