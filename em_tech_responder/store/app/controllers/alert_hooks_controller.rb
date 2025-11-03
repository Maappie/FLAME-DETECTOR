# app/controllers/alert_hooks_controller.rb
class AlertHooksController < ApplicationController
  protect_from_forgery with: :null_session
  skip_before_action :verify_authenticity_token
  before_action :verify_em_signature!

  def fire
    raw = request.body.read
    request.body.rewind

    payload =
      if request.content_type.to_s.include?("application/json")
        JSON.parse(raw) rescue {}
      else
        params.to_unsafe_h
      end

    alert = payload["alert"] || {}

    id         = alert["id"]
    sender_tag = alert["sender_tag"]
    message    = alert["message"]
    created_at = alert["created_at"]

    parsed_alert_at =
      begin
        created_at.present? ? Time.iso8601(created_at) : nil
      rescue ArgumentError, TypeError
        nil
      end

    AlertReceipt.create!(
      alert_id:    id,
      sender_tag:  sender_tag,
      message:     message,
      alert_at:    parsed_alert_at,
      received_at: Time.current
    )

    # 👇 call service object
    Esp32Notify.call(sender_tag: sender_tag, message: message)

    render json: { ok: true }, status: :ok
  rescue => e
    Rails.logger.warn { "[AlertHooks] error: #{e.class}: #{e.message}" }
    render json: { ok: false, error: e.message }, status: :bad_request
  end

  private

  def verify_em_signature!
    secret = Rails.configuration.x.try(:alerts).try(:webhook_secret)
    return true if secret.blank?

    ts  = request.get_header("HTTP_X_EM_TIMESTAMP").to_s
    sig = request.get_header("HTTP_X_EM_SIGNATURE").to_s
    raw = request.body.read
    request.body.rewind

    if ts.blank? || sig.blank? || !sig.start_with?("sha256=")
      render json: { ok: false, error: "missing headers" }, status: :unauthorized and return
    end

    begin
      tsi = Integer(ts)
      if (Time.now.to_i - tsi).abs > 300
        render json: { ok: false, error: "stale timestamp" }, status: :unauthorized and return
      end
    rescue
      render json: { ok: false, error: "bad timestamp" }, status: :unauthorized and return
    end

    expected = "sha256=" + OpenSSL::HMAC.hexdigest("SHA256", secret, "#{ts}.#{raw}")
    unless secure_compare(sig, expected)
      render json: { ok: false, error: "bad signature" }, status: :unauthorized and return
    end
  end

  def secure_compare(a, b)
    ActiveSupport::SecurityUtils.secure_compare(a.to_s, b.to_s)
  rescue
    false
  end
end
