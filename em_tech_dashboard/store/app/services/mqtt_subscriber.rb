require "mqtt"
require "json"
require "timeout"

class MqttSubscriber

  def self.start
    $stdout.sync = true

    mqtt_config = Rails.configuration.x.mqtt

    loop do
      begin
        puts "[MQTT] connecting to #{mqtt_config.host}:#{mqtt_config.port}…"
        client = MQTT::Client.new(
          host: mqtt_config.host,
          port: mqtt_config.port,
          username: mqtt_config.username,
          password: mqtt_config.password,
          keep_alive: 30,
          client_id: "rails-subscriber",
          clean_session: false
        )

        # Manual connect timeout (5s)
        Timeout.timeout(5) { client.connect }
        puts "[MQTT] connected. subscribing #{mqtt_config.topic} (QoS=#{mqtt_config.qos})"
        client.subscribe(mqtt_config.topic => mqtt_config.qos)

        client.get do |_topic, payload|
          puts "[MQTT] recv #{payload.bytesize}B"
          save_payload(payload)
        end

      rescue Timeout::Error
        puts "[MQTT] connect timeout after 5s — retrying in 3s"
        sleep 3
      rescue => e
        puts "[MQTT] error: #{e.class}: #{e.message} — retrying in 3s"
        sleep 3
      end
    end
  end

# services/mqtt_subscriber.rb (only the save method changed at the bottom)
  def self.save_payload(payload)
    d = JSON.parse(payload) rescue {"message" => payload.to_s}

    msg = Message.create!(
      sender_tag:  d["sender_tag"],
      message:     d["message"] || d["text"] || d["msg"],
      raw_payload: payload
    )

    # Kick the DB-side detector
    AlertDetector.process_new_message(msg)
  rescue => e
    puts "[MQTT] save failed: #{e.class}: #{e.message}"
  end

end
