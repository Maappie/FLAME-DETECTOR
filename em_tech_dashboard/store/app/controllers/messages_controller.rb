class MessagesController < ApplicationController
  def index
    limit = params.fetch(:limit, 200).to_i.clamp(1, 500)

    scope =
      if params[:since_id].present?
        # Safer against clock ties: created_at + id tiebreaker
        if (anchor = Message.select(:id, :created_at).find_by(id: params[:since_id]))
          Message.where(
            "created_at > :t OR (created_at = :t AND id > :id)",
            t: anchor.created_at, id: anchor.id
          )
        else
          Message.all
        end
      elsif params[:since].present?
        # Optional: ISO time filter, less robust than since_id if timestamps tie
        begin
          t = Time.iso8601(params[:since])
          Message.where("created_at > ?", t)
        rescue ArgumentError
          Message.all
        end
      else
        Message.all
      end

    @messages = scope.order(created_at: :desc, id: :desc).limit(limit)

    # Return only fields the UI needs (smaller payloads)
    render json: @messages.as_json(only: [:id, :created_at, :sender_tag, :level, :zone, :message, :nonce])
  end

  def show
    @message = Message.find(params[:id])
    render json: @message
  end
end
