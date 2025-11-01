class CreateAlerts < ActiveRecord::Migration[8.0]
  def change
    create_table :alerts do |t|
      t.integer :start_second, null: false   # epoch seconds (burst start t)
      t.integer :end_second,   null: false   # epoch seconds (t+2)
      t.bigint  :rep_message_id             # representative message id within [t, t+2]
      t.timestamps
    end

    add_index :alerts, :start_second, unique: true
    add_index :alerts, :end_second
    add_foreign_key :alerts, :messages, column: :rep_message_id
  end
end
