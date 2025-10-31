import os
import time
from datetime import datetime
import cv2
import zmq
from ultralytics import YOLO

from .config import (
    MODEL_PATH, CONF_THRESH, FIRE_LABELS,
    SAVE_VIDEO, VIDEO_FILENAME, VIDEO_FPS_FALLBACK,
    GRID_ROWS, GRID_COLS, LINE_COLOR, LINE_THICKNESS,
    SHOW_NUMBERS_DEFAULT,
)
from .camera import (
    rotate_if_needed, draw_grid, draw_axis_numbers_pixels, quadrant_zone,
    open_camera_and_probe,
)
from .mqtt_broker import publish_esp32, publish_rails


# --- ZMQ publish settings (stream.py will SUBSCRIBE to this) ---
ZMQ_BIND      = os.getenv("ZMQ_BIND", "tcp://127.0.0.1:5556")  # local-only
ZMQ_SNDHWM    = int(os.getenv("ZMQ_SNDHWM", "2"))              # drop old frames
PUBLISH_EVERY = int(os.getenv("PUBLISH_EVERY", "1"))           # send every Nth frame


def main():
    # Init model
    model = YOLO(MODEL_PATH)

    # Open webcam + get first rotated frame
    cap, frame, w, h = open_camera_and_probe()

    # ZMQ PUB socket (so stream.py can serve MJPEG without touching the camera)
    ctx = zmq.Context.instance()
    pub = ctx.socket(zmq.PUB)
    pub.setsockopt(zmq.SNDHWM, ZMQ_SNDHWM)
    pub.bind(ZMQ_BIND)
    print(f"[ZMQ] Publishing annotated JPEG frames on {ZMQ_BIND} (every {PUBLISH_EVERY} frame)")

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

            # --- Publish per-zone notifications to ESP32 ---
            if zones_with_fire:
                for z in sorted(zones_with_fire):
                    publish_esp32(z)

                    publish_rails({
                        "sender_tag": "yolo-fire-detector-01",
                        "message":    "FIRE DETECTED",
                        "level":      "alert",
                        "zones":      sorted(zones_with_fire)  # plural
                    })

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

            # --- Publish annotated frame to stream.py via ZMQ (as JPEG) ---
            if frame_idx % PUBLISH_EVERY == 0:
                ok, jpg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                if ok:
                    try:
                        pub.send(jpg.tobytes(), flags=zmq.NOBLOCK)
                    except zmq.Again:
                        pass  # drop if subscriber is slow

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
        try:
            cap.release()
        except Exception:
            pass
        if writer_out is not None:
            try:
                writer_out.release()
            except Exception:
                pass
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        try:
            pub.close(0)
            # ctx.term()  # optional; Context.instance() is shared, so skip in multi-module apps
        except Exception:
            pass


if __name__ == "__main__":
    main()
