# mqtt_broker.py

from .config import (
    MQTT_ENABLE_ESP32, MQTT_ENABLE_RAILS,
    MQTT_USER, MQTT_PASS, MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE,
    TOPIC_ESP32, TOPIC_RAILS, CLIENT_ID_ESP32, CLIENT_ID_RAILS
)

_mqtt_client_esp32 = None
_mqtt_client_rails = None


def _ensure_paho():
    """Return True if paho-mqtt is available; print hint otherwise."""
    global mqtt
    try:
        import paho.mqtt.client as mqtt  # noqa: F401
        return True
    except Exception:
        print("[WARN] paho-mqtt not installed. Run: pip install paho-mqtt")
        return False


def _mqtt_connect(client_id):
    """
    Connect non-fatally. Return client or None if broker is unavailable.
    Uses loop_start() so publish() is non-blocking.
    """
    try:
        import paho.mqtt.client as mqtt
        c = mqtt.Client(client_id=client_id, clean_session=True)
        c.username_pw_set(MQTT_USER, MQTT_PASS)
        c.connect(MQTT_HOST, MQTT_PORT, keepalive=MQTT_KEEPALIVE)  # may raise if broker down
        c.loop_start()
        return c
    except Exception as e:
        print(f"[WARN] MQTT connect failed for {client_id}: {e}. Will retry later.")
        return None


def publish_esp32(zone_text):
    """
    Send compact payload to ESP32 like: {fire}{top-left}
    Retain=True so devices subscribing later still get the last state.
    """
    global _mqtt_client_esp32
    if not MQTT_ENABLE_ESP32 or not _ensure_paho():
        return

    if _mqtt_client_esp32 is None:
        _mqtt_client_esp32 = _mqtt_connect(CLIENT_ID_ESP32)
        if _mqtt_client_esp32 is None:
            return  # broker unavailable → skip this publish, keep app running

    payload = f"{{fire}}{{{str(zone_text).lower()}}}"
    try:
        _mqtt_client_esp32.publish(TOPIC_ESP32, payload, qos=1, retain=True)
    except Exception as e:
        print(f"[WARN] ESP32 publish failed: {e}. Will reconnect on next event.")
        # reset client so we attempt a fresh connect next time
        try:
            _mqtt_client_esp32.loop_stop()
        except Exception:
            pass
        _mqtt_client_esp32 = None


# ===== Rails publisher (JSON) =====

import json
import uuid
import time


def publish_rails(json_dict):
    """
    Publish richer JSON for the Rails worker to ingest.
    Defaults added if missing:
      - sender_tag: "yolo-fire-detector-01"
      - message:    "event"
      - level:      "info"
      - zone:       None
      - nonce:      random hex (Rails can unique-index on this)
      - ts:         ISO8601 UTC (YYYY-MM-DDTHH:MM:SSZ)

    Uses QoS=1, retain=False to avoid replay storms when the subscriber reconnects.
    """
    global _mqtt_client_rails
    if not MQTT_ENABLE_RAILS or not _ensure_paho():
        return

    # IMPORTANT:
    # Ensure CLIENT_ID_RAILS here (publisher) differs from the Rails subscriber's client_id.
    # Example:
    #   - Python publisher (this file): CLIENT_ID_RAILS = "rails-publisher"
    #   - Rails subscriber (Ruby):      client_id: "rails-subscriber"
    if _mqtt_client_rails is None:
        _mqtt_client_rails = _mqtt_connect(CLIENT_ID_RAILS)
        if _mqtt_client_rails is None:
            return  # broker unavailable → skip this publish

    # Normalize payload
    payload = dict(json_dict or {})
    payload.setdefault("sender_tag", "yolo-fire-detector-01")
    payload.setdefault("message", "event")
    payload.setdefault("level", "info")
    payload.setdefault("zone", None)
    payload.setdefault("nonce", uuid.uuid4().hex)
    payload.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    try:
        _mqtt_client_rails.publish(
            TOPIC_RAILS,
            json.dumps(payload, separators=(",", ":")),
            qos=1,
            retain=False
        )
    except Exception as e:
        print(f"[WARN] Rails publish failed: {e}. Will reconnect on next event.")
        try:
            _mqtt_client_rails.loop_stop()
        except Exception:
            pass
        _mqtt_client_rails = None
