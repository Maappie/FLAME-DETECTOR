Rails.application.routes.draw do
  get "/camera", to: "cameras#show"
  get "/camera/health", to: "cameras#health"

  resources :messages, only: [:index, :show]
end
