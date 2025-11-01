# app/services/http_notifier.rb
require "net/http"
require "uri"
require "json"
require "openssl"

class HttpNotifier
  DEFAULT_URL = "http://127.0.0.1:4000/alert_hooks/fire"

  def self.notify_fire(alert)
    rep = alert.respond_to?(:rep_message) ? alert.rep_message : nil

    payload = {
      event: "fire_alert",
      alert: {
        id:         alert.id,
        sender_tag: rep&.sender_tag,
        message:    rep&.message,
        created_at: alert.created_at&.iso8601
      }
    }

    url =
      Rails.configuration.x.try(:alerts).try(:webhook_url) ||
      ENV["ALERT_WEBHOOK_URL"].presence ||
      DEFAULT_URL

    if ENV["SEND_ALERT_SYNC"] == "1"
      post_json(url: url, payload: payload, timeout: 5)
    else
      Thread.new { post_json(url: url, payload: payload, timeout: 2) rescue nil }
    end
  end

  def self.post_json(url:, payload:, timeout:)
    body = JSON.dump(payload)
    ts   = Time.now.to_i.to_s
    sec  = (Rails.configuration.x.try(:alerts).try(:webhook_secret) || ENV["ALERT_WEBHOOK_SECRET"].to_s)
    sig  = sec.present? ? OpenSSL::HMAC.hexdigest("SHA256", sec, "#{ts}.#{body}") : ""

    uri  = URI.parse(url)
    http = Net::HTTP.new(uri.host, uri.port)
    http.use_ssl      = (uri.scheme == "https")
    http.open_timeout = timeout
    http.read_timeout = timeout

    req = Net::HTTP::Post.new(uri.request_uri)
    req["Content-Type"]   = "application/json"
    req["X-EM-Timestamp"] = ts
    req["X-EM-Signature"] = "sha256=#{sig}" if sec.present?
    req.body = body

    resp = http.request(req)
    Rails.logger.info { "[HttpNotifier] POST #{url} -> #{resp.code}" }
    resp
  end
end
