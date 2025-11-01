# app/controllers/alerts_controller.rb
class AlertsController < ApplicationController
  def index
    alerts = Alert.order(start_second: :desc).limit(10).includes(:rep_message)

    render json: alerts.map { |a|
      rep = a.rep_message
      {
        id: a.id,
        start_second: a.start_second,
        end_second: a.end_second,
        created_at: a.created_at,
        representative: rep && {
          id: rep.id,
          sender_tag: rep.sender_tag,
          message: rep.message,
          created_at: rep.created_at
        }
      }
    }
  end
end
