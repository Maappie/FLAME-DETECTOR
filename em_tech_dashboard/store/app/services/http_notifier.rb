# app/services/http_notifier.rb
require "net/http"
require "uri"
require "json"

class HttpNotifier
  DEFAULT_URL = "http://127.0.0.1:4000/alert_hooks/fire"

  def self.notify_fire(alert)
    # Prefer Alert#rep_message if present; otherwise nil-safe
    rep = alert.respond_to?(:rep_message) ? alert.rep_message : nil

    payload = {
      event: "fire_alert",
      alert: {
        id:         alert.id,
        sender_tag: rep&.sender_tag,    # nil if no rep
        message:    rep&.message,       # nil if no rep
        created_at: alert.created_at&.iso8601
      }
    }
    
    url =
      ENV["ALERT_WEBHOOK_URL"].presence ||
      Rails.configuration.x.try(:alerts).try(:webhook_url) ||
      DEFAULT_URL

      # app/services/http_notifier.rb (inside notify_fire, before Thread.new)
      Rails.logger.info { "[HttpNotifier] will POST to #{url}" }

    Thread.new do
      begin
        post_json(url: url, payload: payload, timeout: 2)
      rescue => e
        Rails.logger.warn { "[HttpNotifier] POST failed: #{e.class}: #{e.message}" }
      end
    end
  end

  def self.post_json(url:, payload:, timeout: 2)
    uri = URI.parse(url)
    http = Net::HTTP.new(uri.host, uri.port)
    http.use_ssl = (uri.scheme == "https")
    http.open_timeout = timeout
    http.read_timeout = timeout

    req = Net::HTTP::Post.new(uri.request_uri)
    req["Content-Type"] = "application/json"
    req.body = JSON.dump(payload)

    resp = http.request(req)
    Rails.logger.info { "[HttpNotifier] POST #{url} -> #{resp.code}" }
    resp
  end
end
