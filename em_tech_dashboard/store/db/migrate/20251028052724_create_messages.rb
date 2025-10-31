class CreateMessages < ActiveRecord::Migration[8.0]
  def change
    create_table :messages do |t|
      t.string :sender_tag
      t.string :nonce
      t.text :message
      t.string :level
      t.string :zone
      t.text :raw_payload

      t.timestamps
    end
  end
end
