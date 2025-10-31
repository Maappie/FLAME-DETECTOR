import cv2
from datetime import datetime

from .config import (
    CAMERA_SOURCE, CAP_BACKEND,
    FORCE_PORTRAIT, ROTATE_DIRECTION,
    GRID_ROWS, GRID_COLS, LINE_THICKNESS, LINE_COLOR,
    SHOW_NUMBERS_DEFAULT, NUM_COLOR, NUM_BG, NUM_THICKNESS,
)

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

def open_camera_and_probe():
    """Open camera and return (cap, first_rotated_frame, width, height)."""
    cap = cv2.VideoCapture(CAMERA_SOURCE, CAP_BACKEND)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera: {CAMERA_SOURCE!r}")
    ret, test_frame = cap.read()
    if not ret:
        cap.release()
        raise RuntimeError("Webcam returned no frames.")
    test_frame = rotate_if_needed(test_frame)
    h, w = test_frame.shape[:2]
    return cap, test_frame, w, h
