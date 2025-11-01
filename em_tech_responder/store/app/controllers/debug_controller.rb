class DebugController < ApplicationController
  # absolutely disable CSRF for webhooks/tests
  protect_from_forgery with: :null_session
  skip_before_action :verify_authenticity_token

  def echo
    raw = request.body.read
    ct  = request.content_type

    Rails.logger.info { "[DEBUG#echo] CT=#{ct.inspect} RAW=#{raw.inspect}" }

    render json: {
      ok: true,
      content_type: ct,
      raw_body: raw,
      params_seen_by_rails: params.except(:controller, :action)
    }, status: :ok
  end
end
