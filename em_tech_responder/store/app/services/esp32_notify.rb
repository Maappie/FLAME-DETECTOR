# app/services/esp32_notify.rb
require "net/http"
require "uri"
require "json"

class Esp32Notify
  def self.call(sender_tag:, message:)
    new(sender_tag, message).send
  end

  def initialize(sender_tag, message)
    @sender_tag = sender_tag
    @message = message
    cfg = Rails.configuration.x.esp32
    @primary_url = cfg.try(:endpoint)
    @fallback_url = cfg.try(:fallback_endpoint)
  end

  def send
    return unless @primary_url.present?

    success = post_to(@primary_url)
    return true if success

    # Try fallback if available
    if @fallback_url.present?
      Rails.logger.warn("[ESP32Notify] Primary endpoint failed, trying fallback...")
      post_to(@fallback_url)
    else
      false
    end
  end

  private

  def post_to(url)
    uri = URI.parse(url)
    http = Net::HTTP.new(uri.host, uri.port)
    http.open_timeout = 1
    http.read_timeout = 2

    req = Net::HTTP::Post.new(uri.path, { "Content-Type" => "application/json" })
    req.body = { sender_tag: @sender_tag, message: @message }.to_json

    response = http.request(req)
    if response.is_a?(Net::HTTPSuccess)
      Rails.logger.info("[ESP32Notify] Successfully sent alert to #{url}")
      true
    else
      Rails.logger.warn("[ESP32Notify] ESP32 responded with #{response.code} #{response.message}")
      false
    end
  rescue => e
    Rails.logger.warn("[ESP32Notify] Failed to notify #{url}: #{e.class} - #{e.message}")
    false
  end
end
