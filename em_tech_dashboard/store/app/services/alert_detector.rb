# app/services/alert_detector.rb
class AlertDetector
  class << self
    def process_new_message(message)
      s = message.created_at.to_i
      [s - 2, s - 1, s].each { |t| try_accept_burst(t) }
    end

    private

    def try_accept_burst(t)
      t = t.to_i
      return if t < 0

      # --- Quiet gate based on the *latest* FIRE since last burst ---
      last = Alert.order(:start_second).last
      if last
        latest_fire = Message.fire_like
          .where("created_at > ? AND created_at < ?", Time.at(last.end_second), Time.at(t))
          .order(created_at: :desc, id: :desc)
          .limit(1)
          .pick(:created_at)
        latest_fire_sec = (latest_fire || Time.at(last.end_second)).to_i

        earliest_allowed = latest_fire_sec + 6
        if t < earliest_allowed
          Rails.logger.debug { "[AlertDetector] REJECT t=#{t} (< earliest_allowed=#{earliest_allowed} from latest_fire_sec=#{latest_fire_sec})" }
          return
        end
      else
        Rails.logger.debug { "[AlertDetector] no previous alert; candidate_t=#{t}" }
      end

      # --- Burst rule: FIRE-like present in each second t, t+1, t+2 ---
      unless fire_each_second?(t, t + 1, t + 2)
        Rails.logger.debug { "[AlertDetector] skip t=#{t}: missing per-second FIRE presence" }
        return
      end

      rep = Message.pick_rep_in_window(t)
      alert = Alert.create!(start_second: t, end_second: t + 2, rep_message_id: rep&.id)
      Rails.logger.info { "[AlertDetector] ACCEPT t=#{t}..#{t + 2} rep=#{rep&.id}" }

      # >>> NEW: notify external server (non-blocking)
      HttpNotifier.notify_fire(alert)

    rescue => e
      Rails.logger.warn("[AlertDetector] #{e.class}: #{e.message}")
    end

    def fire_each_second?(*seconds)
      seconds.all? { |sec| Message.fire_like_exists_in_second?(sec) }
    end
  end
end
