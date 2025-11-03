# config/routes.rb
Rails.application.routes.draw do
  post "/alert_hooks/fire", to: "alert_hooks#fire"
  post "/__debug__/echo", to: "debug#echo"

  # Views to browse received alerts
  resources :alert_receipts, only: [:index, :show]

  # Optional: make the list the homepage
  root "alert_receipts#index"

  get "/time", to: proc { [200, { "Content-Type" => "application/json" }, [Time.now.to_i.to_s]] }


  # Turbo
  mount ActionCable.server => "/cable"
  
end
