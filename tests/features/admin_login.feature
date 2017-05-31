Feature: Logging into Admin Panel
  Regular users should not be able to log into the Admin panel while staff and superusers should
  be able to.

  Scenario: Logging in as admin
    Given I'm a super user
    And I log in
    Then Login should succeed

  Scenario: Logging in as staff
    Given I'm a staff user
    And I log in
    Then Login should succeed

  Scenario: Logging in as regular user
    Given I'm a regular user
    And I log in
    Then Login should not succeed
