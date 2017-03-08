Feature: API
  All API urls should be accessible and not raise errors

  Background:
    Given I'm a regular user
    And I request an auth token

  Scenario: Login via API
    Then I should be able to access my profile API


  Scenario Outline: Access APIs
    Then I should be able to access the API <api>

    Examples:
      | api                 |
      | assets              |
      | calendar_assets     |
      | device_groups       |
      | device_screenshots  |
      | devices             |
      | feed_assets         |
      | image_assets        |
      | playlist_items      |
      | playlists           |
      | ticker_series       |
      | tickers             |
      | video_assets        |
      | web_asset_templates |
      | web_assets          |
