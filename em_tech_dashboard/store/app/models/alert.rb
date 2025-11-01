# app/models/alert.rb
class Alert < ApplicationRecord
  belongs_to :rep_message, class_name: "Message", optional: true
  validates :start_second, :end_second, presence: true
  validates :start_second, uniqueness: true

end
