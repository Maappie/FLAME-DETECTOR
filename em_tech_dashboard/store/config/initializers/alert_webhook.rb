# config/initializers/alert_webhook.rb
Rails.application.configure do
  # Only set a default secret here; do NOT re-set the URL if it's already in env files
  config.x.alerts.webhook_secret ||= "EMTECH_http_sending_token_key123"
  # Optional: fallback URL ONLY if none set in the env files
  config.x.alerts.webhook_url ||= "http://127.0.0.1:4000/alert_hooks/fire"
end
