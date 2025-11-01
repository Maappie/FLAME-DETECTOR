# config/initializers/alert_webhook.rb
Rails.application.configure do
  # Keep your per-env URL in config/environments/*.rb
  # Only ensure a secret exists here (or override per env if you prefer).
  config.x.alerts.webhook_secret ||= "EMTECH_http_sending_token_key123"
end
