import time
from datetime import datetime
import os
import cv2
from ultralytics import YOLO

# --- CONFIG ---
MODEL_PATH = r"C:\Users\Renz\CODES\FLAME-DETECTOR\-FLAME_DETECTOR\best.pt"
CONF_THRESH = 0.3
FIRE_LABELS = {"fire", "flame", "flames"}  # change to your exact class name(s)

# Camera (Windows example)
CAMERA_SOURCE = 1               # or 'video=Iriun Webcam'
CAP_BACKEND   = cv2.CAP_DSHOW   # Windows DirectShow. macOS: CAP_AVFOUNDATION, Linux: CAP_V4L2

# Optional: ask the camera for this size (not all drivers honor it)
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
LINE_COLOR = (0, 255, 255)   # BGR (yellow)

SHOW_NUMBERS_DEFAULT = True
NUM_COLOR = (255, 255, 255)  # text color
NUM_BG = (0, 0, 0)           # background box
NUM_THICKNESS = 2

# --- ORIENTATION ---
FORCE_PORTRAIT = True          # set False to keep native landscape
# Options: 'cw' (90° clockwise), 'ccw' (90° counter-clockwise), '180'
ROTATE_DIRECTION = 'cw'

def rotate_if_needed(img):
    if not FORCE_PORTRAIT:
        return img
    if ROTATE_DIRECTION == 'cw':
        return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    elif ROTATE_DIRECTION == 'ccw':
        return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif ROTATE_DIRECTION == '180':
        return cv2.rotate(img, cv2.ROTATE_180)
    return img  # fallback


# ---------------- MQTT (ESP32 now, Rails later) ----------------
# Enable/disable independent publishers
MQTT_ENABLE_ESP32 = True
MQTT_ENABLE_RAILS = False  # keep False for now; flip to True when ready

# Broker settings (point ESP32 + Rails to the same broker)
MQTT_HOST = "192.168.68.110"   # your laptop LAN IP
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

# Lazy init holders
_mqtt_client_esp32 = None
_mqtt_client_rails = None

def _ensure_paho():
    global mqtt
    try:
        import paho.mqtt.client as mqtt  # noqa: F401
        return True
    except Exception:
        print("[WARN] paho-mqtt not installed. Run: pip install paho-mqtt")
        return False

def _mqtt_connect(client_id):
    import paho.mqtt.client as mqtt
    c = mqtt.Client(client_id=client_id, clean_session=True)
    # >>> add creds BEFORE connect <<<
    c.username_pw_set(MQTT_USER, MQTT_PASS)
    c.connect(MQTT_HOST, MQTT_PORT, keepalive=MQTT_KEEPALIVE)
    c.loop_start()
    return c

def publish_esp32(zone_text):
    """Send compact payload to ESP32 like: {fire}{top-left}"""
    global _mqtt_client_esp32
    if not MQTT_ENABLE_ESP32 or not _ensure_paho():
        return
    if _mqtt_client_esp32 is None:
        _mqtt_client_esp32 = _mqtt_connect(CLIENT_ID_ESP32)

    payload = f"{{fire}}{{{zone_text.lower()}}}"
    try:
        _mqtt_client_esp32.publish(TOPIC_ESP32, payload, qos=1, retain=True)
        # print(f"[MQTT→ESP32] {TOPIC_ESP32}: {payload}")
    except Exception as e:
        print(f"[WARN] ESP32 publish failed: {e}")

def publish_rails(json_dict):
    """Future use: publish richer JSON for Rails worker to ingest."""
    global _mqtt_client_rails
    if not MQTT_ENABLE_RAILS or not _ensure_paho():
        return
    if _mqtt_client_rails is None:
        _mqtt_client_rails = _mqtt_connect(CLIENT_ID_RAILS)
    try:
        import json
        _mqtt_client_rails.publish(TOPIC_RAILS, json.dumps(json_dict), qos=1, retain=True)
    except Exception as e:
        print(f"[WARN] Rails publish failed: {e}")
# ---------------------------------------------------------------


# --- HELPERS (grid + labels) ---
def put_text_with_bg(img, text, org, font_scale, color, thickness, bg):
    (tw, th), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
    x, y = org
    cv2.rectangle(img, (x - 3, y - th - 4), (x + tw + 3, y + baseline + 3), bg, -1)
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)

def draw_grid(frame, rows, cols, color, thickness):
    h, w = frame.shape[:2]
    for c in range(1, cols):
        x = int(w * c / cols)
        cv2.line(frame, (x, 0), (x, h), color, thickness, lineType=cv2.LINE_AA)
    for r in range(1, rows):
        y = int(h * r / rows)
        cv2.line(frame, (0, y), (w, y), color, thickness, lineType=cv2.LINE_AA)
    cv2.rectangle(frame, (0, 0), (w - 1, h - 1), color, thickness, cv2.LINE_AA)

def draw_axis_numbers_pixels(frame, rows, cols):
    h, w = frame.shape[:2]
    font_scale = max(0.5, min(w, h) / 800.0)

    for c in range(cols + 1):
        x = int(round(w * c / cols))
        label = str(x)
        x_text = min(max(2, x - 8), w - 40)
        put_text_with_bg(frame, label, (x_text, 22), font_scale, NUM_COLOR, NUM_THICKNESS, NUM_BG)

    for r in range(rows + 1):
        y = int(round(h * r / rows))
        label = str(y)
        y_text = max(22, min(h - 6, y + 6))
        put_text_with_bg(frame, label, (6, y_text), font_scale, NUM_COLOR, NUM_THICKNESS, NUM_BG)

def quadrant_zone(cx, cy, w, h):
    """
    Return quadrant for a fixed 2x2 grid:
      Top-Left, Top-Right, Bottom-Left, Bottom-Right
    """
    mid_x = w / 2.0
    mid_y = h / 2.0
    horiz = "Left" if cx < mid_x else "Right"
    vert = "Top" if cy < mid_y else "Bottom"
    return f"{vert}-{horiz}"


# --- MAIN ---
def main():
    # Init model
    model = YOLO(MODEL_PATH)

    # Open webcam
    cap = cv2.VideoCapture(CAMERA_SOURCE, CAP_BACKEND)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera: {CAMERA_SOURCE!r}")

    # Optional: request resolution (driver may ignore)
    # try:
    #     cap.set(cv2.CAP_PROP_FRAME_WIDTH, DESIRED_W)
    #     cap.set(cv2.CAP_PROP_FRAME_HEIGHT, DESIRED_H)
    # except NameError:
    #     pass  # DESIRED_W/H not defined

    # Probe one frame for dimensions
    ret, test_frame = cap.read()
    if not ret:
        cap.release()
        raise RuntimeError("Webcam returned no frames.")

    # Rotate first frame BEFORE using size
    test_frame = rotate_if_needed(test_frame)
    h, w = test_frame.shape[:2]

    # Optional VideoWriter (use rotated size)
    writer_out = None
    if SAVE_VIDEO:
        fps = cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 1.0:
            fps = VIDEO_FPS_FALLBACK
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer_out = cv2.VideoWriter(VIDEO_FILENAME, fourcc, fps, (w, h))
        print(f"[INFO] Saving annotated video to: {VIDEO_FILENAME}")

    print("[INFO] Press 'q' to quit, 'g' to toggle grid, 'n' to toggle numbers.")
    frame_idx = 0
    start = time.time()

    # Grid toggles
    show_grid = True
    show_numbers = SHOW_NUMBERS_DEFAULT

    try:
        frame = test_frame  # show first rotated frame immediately

        while True:
            if frame_idx > 0:
                ret, frame = cap.read()
                if not ret:
                    break
                frame = rotate_if_needed(frame)  # rotate each new frame

            # Run YOLO on this (possibly rotated) frame
            results = model.predict(
                source=frame,
                conf=CONF_THRESH,
                verbose=False
            )
            result = results[0]
            names = result.names

            # Track zones with fire in this frame to avoid duplicate publishes
            zones_with_fire = set()

            # Draw detections
            if result.boxes is not None:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    label = names.get(cls_id, str(cls_id))

                    # Only consider fire labels
                    if label.lower() not in FIRE_LABELS:
                        continue

                    # Get coordinates + confidence
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)
                    conf = float(box.conf[0])

                    # Draw rectangle + label with confidence
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
                    text = f"{label} {conf:.2f}"
                    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                    cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 6, y1), (0, 0, 0), -1)
                    cv2.putText(frame, text, (x1 + 3, y1 - 6),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                    # Determine 2x2 quadrant for the center
                    zone = quadrant_zone(cx, cy, w, h)
                    zones_with_fire.add(zone)

                    # Console print: timestamp + bbox + center + zone
                    now_iso = datetime.now().isoformat(timespec="seconds")
                    print(f"{now_iso}, x1={x1}, y1={y1}, x2={x2}, y2={y2}, cx={cx}, cy={cy}, zone={zone}")

            # --- NEW: Publish per-zone notifications to ESP32 ---
            # Example payload per zone: {fire}{top-left}
            if zones_with_fire:
                for z in sorted(zones_with_fire):
                    publish_esp32(z)

                # (Future) Publish richer JSON to Rails, disabled by default:
                # publish_rails({
                #     "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                #     "zones": sorted(zones_with_fire),
                #     "note": "fire detected"
                # })

            # FPS overlay
            elapsed = time.time() - start
            fps_est = frame_idx / elapsed if elapsed > 0 else 0.0
            cv2.putText(frame, f"FPS: {fps_est:.1f}", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            # Draw 2x2 grid + pixel ticks (optional)
            if show_grid:
                draw_grid(frame, GRID_ROWS, GRID_COLS, LINE_COLOR, LINE_THICKNESS)
            if show_numbers:
                draw_axis_numbers_pixels(frame, GRID_ROWS, GRID_COLS)

            # Optional write to video
            if writer_out is not None:
                writer_out.write(frame)

            # Show window
            cv2.imshow("YOLO Fire Detection + 2x2 Grid (Portrait Ready)", frame)

            frame_idx += 1
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('g'):
                show_grid = not show_grid
            elif key == ord('n'):
                show_numbers = not show_numbers

    finally:
        cap.release()
        if writer_out is not None:
            writer_out.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
