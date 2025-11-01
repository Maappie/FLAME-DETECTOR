# app/models/message.rb
class Message < ApplicationRecord
  FIRE_TERMS = %w[fire flame].freeze

  scope :fire_like, -> {
    ors = FIRE_TERMS.map { |term|
      arel_table[:message].lower.matches("%#{term}%")
      .or(arel_table[:raw_payload].lower.matches("%#{term}%"))
    }
    where(ors.inject { |acc, expr| acc.or(expr) })
  }

  # Any FIRE-like within [sec, sec+1)
  def self.fire_like_exists_in_second?(sec)
    where("created_at >= ? AND created_at < ?", Time.at(sec), Time.at(sec + 1))
      .merge(fire_like)
      .exists?
  end

  # Pick representative FIRE-like within [t, t+3)
  def self.pick_rep_in_window(start_sec)
    where("created_at >= ? AND created_at < ?", Time.at(start_sec), Time.at(start_sec + 3))
      .merge(fire_like)
      .order(:created_at, :id)
      .first
  end

  # Returns true if there is ANY FIRE-like in [a, b) **by absolute time**.
  # Use integer-seconds boundaries with Time.at(a/b) when you call it.
  def self.any_fire_in_time_window?(from_inclusive_sec, to_exclusive_sec)
    return false if to_exclusive_sec <= from_inclusive_sec
    where("created_at >= ? AND created_at < ?", Time.at(from_inclusive_sec), Time.at(to_exclusive_sec))
      .merge(fire_like)
      .exists?
  end
end
