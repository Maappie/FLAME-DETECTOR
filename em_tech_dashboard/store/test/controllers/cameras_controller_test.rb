require "test_helper"

class CamerasControllerTest < ActionDispatch::IntegrationTest
  test "should get show" do
    get cameras_show_url
    assert_response :success
  end
end
