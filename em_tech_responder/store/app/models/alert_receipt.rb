class AlertReceipt < ApplicationRecord
  validates :alert_id, presence: true

  after_create_commit -> {
    broadcast_prepend_to :alerts,
      target: "alerts_table_body",
      partial: "alert_receipts/row",
      locals: { r: self }
  }

   after_update_commit -> {
    broadcast_replace_to :alerts,
      target: dom_id(self),
      partial: "alert_receipts/row",
      locals: { r: self }
  }
end
