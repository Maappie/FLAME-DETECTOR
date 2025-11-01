# app/controllers/alert_receipts_controller.rb
class AlertReceiptsController < ApplicationController
  def index
    @alert_receipts = AlertReceipt.order(created_at: :desc).limit(200)
  end

  def show
    @alert_receipt = AlertReceipt.find(params[:id])
  end
end
