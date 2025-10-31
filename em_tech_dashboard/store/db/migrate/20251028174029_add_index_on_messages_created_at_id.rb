class AddIndexOnMessagesCreatedAtId < ActiveRecord::Migration[8.0]
  def change
    add_index :messages, [:created_at, :id]
  end
end
