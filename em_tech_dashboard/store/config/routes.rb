Rails.application.routes.draw do
  get "alerts/index"
  get "/camera", to: "cameras#show"
  get "/camera/health", to: "cameras#health"

  resources :messages, only: [:index, :show]

  resources :alerts, only: [:index]

  mount ActionCable.server => "/cable"

end
