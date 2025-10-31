require "mqtt"
require "json"
require "timeout"

class MqttSubscriber
  HOST="192.168.68.137"; PORT=1883; USER="iotuser"; PASS="emtech_broker"
  TOPIC="site/lab1/ingest/rails"; QOS=1

  def self.start
    $stdout.sync = true
    loop do
      begin
        puts "[MQTT] connecting to #{HOST}:#{PORT}…"
        client = MQTT::Client.new(
          host: HOST,
          port: PORT,
          username: USER,
          password: PASS,
          keep_alive: 30,
          client_id: "rails-subscriber",
          clean_session: false
        )

        # Manual connect timeout (5s)
        Timeout.timeout(5) { client.connect }
        puts "[MQTT] connected. subscribing #{TOPIC} (QoS=#{QOS})"
        client.subscribe(TOPIC => QOS)

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

  def self.save_payload(payload)
    d = JSON.parse(payload) rescue {"message" => payload.to_s}

    Message.create!(
      sender_tag:  d["sender_tag"],
      message:     d["message"] || d["text"] || d["msg"],
      raw_payload: payload
    )
  rescue => e
    puts "[MQTT] save failed: #{e.class}: #{e.message}"
  end

end
