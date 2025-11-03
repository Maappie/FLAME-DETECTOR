class CamerasController < ApplicationController
  # no Devise auth for now; add when ready

  def show
    @stream_url = ENV.fetch(
      "YOLO_STREAM_URL",
      "http://192.168.68.121:5001/stream.mjpg?token=dev-secret-123"
    )
    # If you already persist messages, load the latest ones here:
    # @messages = Message.order(created_at: :desc).limit(50)
    @messages = [] # placeholder if you don't persist yet
  end

  def health
    render json: { ok: true }
  end
end
