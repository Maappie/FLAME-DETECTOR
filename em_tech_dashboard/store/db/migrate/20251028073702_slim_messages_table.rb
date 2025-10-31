class SlimMessagesTable < ActiveRecord::Migration[8.0]
  def up
    change_table :messages do |t|
      t.remove :nonce, :level, :zone
      t.remove :updated_at
    end
  end

  def down
    change_table :messages do |t|
      t.string :nonce
      t.string :level
      t.string :zone
      t.datetime :updated_at, precision: 6
    end
  end
end
