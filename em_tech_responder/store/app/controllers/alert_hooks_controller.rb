# app/controllers/alert_hooks_controller.rb
class AlertHooksController < ApplicationController
  protect_from_forgery with: :null_session
  skip_before_action :verify_authenticity_token

  def fire
    payload =
      if request.content_type.to_s.include?("application/json")
        JSON.parse(request.body.read) rescue {}
      else
        params.to_unsafe_h
      end

    alert = payload["alert"] || {}

    id         = alert["id"]
    sender_tag = alert["sender_tag"]
    message    = alert["message"]
    created_at = alert["created_at"]

    # Parse created_at safely (avoid inline `rescue` in kwargs)
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

    render json: { ok: true }, status: :ok
  rescue => e
    Rails.logger.warn { "[AlertHooks] error: #{e.class}: #{e.message}" }
    render json: { ok: false, error: e.message }, status: :bad_request
  end
end
