class CamerasController < ApplicationController
  # no Devise auth for now; add when ready

  def show
    @stream_url = Rails.configuration.x.yolo_stream_url
  
    @messages = [] # placeholder if you don't persist yet
  end

  def health
    render json: { ok: true }
  end
end
