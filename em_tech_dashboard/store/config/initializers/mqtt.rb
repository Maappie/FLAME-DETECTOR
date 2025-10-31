# MQTT defaults; ENV can override anytime
Rails.application.configure do
  config.x.mqtt.enabled_rails  = ENV.fetch("MQTT_ENABLE_RAILS", "true") == "true"

  config.x.mqtt.host           = ENV.fetch("MQTT_HOST",     "192.168.68.110")
  config.x.mqtt.port           = Integer(ENV.fetch("MQTT_PORT", "1883"))
  config.x.mqtt.keepalive      = Integer(ENV.fetch("MQTT_KEEPALIVE", "30"))
  config.x.mqtt.username       = ENV.fetch("MQTT_USER", "iotuser")
  config.x.mqtt.password       = ENV.fetch("MQTT_PASS", "emtech_broker")

  # Topics / client id
  config.x.mqtt.topic_rails    = ENV.fetch("TOPIC_RAILS", "site/lab1/ingest/rails")
  config.x.mqtt.client_id      = ENV.fetch("CLIENT_ID_RAILS", "yolo-pub-rails") # can be any unique string

  # Persistence / robustness
  config.x.mqtt.clean_session  = ENV.fetch("MQTT_CLEAN_SESSION", "false") == "true" # false helps with QoS1 redelivery
  config.x.mqtt.qos            = Integer(ENV.fetch("MQTT_QOS", "1"))
end
