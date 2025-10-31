import paho.mqtt.client as mqtt

MQTT_HOST = "192.168.68.110"
MQTT_PORT = 1883
MQTT_USER = "iotuser"
MQTT_PASS = "emtech_broker"
TOPIC = "site/lab1/devices/esp32-01/in"

def on_connect(c,u,f,rc,props=None):
    print("on_connect rc:", rc)

c = mqtt.Client(client_id="pub-check")
c.username_pw_set(MQTT_USER, MQTT_PASS)
c.enable_logger()  # show paho logs
c.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
c.loop_start()
info = c.publish(TOPIC, "{fire}{top-left}", qos=1, retain=False)
info.wait_for_publish()
print("published:", info.is_published())
c.loop_stop(); c.disconnect()
