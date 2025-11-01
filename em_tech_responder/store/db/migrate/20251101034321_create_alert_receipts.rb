class CreateAlertReceipts < ActiveRecord::Migration[8.0]
  def change
    create_table :alert_receipts do |t|
      t.integer :alert_id
      t.string :sender_tag
      t.text :message
      t.datetime :alert_at
      t.datetime :received_at

      t.timestamps
    end
  end
end
