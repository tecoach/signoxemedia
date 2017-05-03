Feature: Admin Panel pages
  All Admin Panel pages should be accessible and not raise errors

  Scenario Outline: Access Admin Pages
    Given I'm a super user
    And I log in
    Then I should be able to access <page> of <app>
    And Access the add page

    Examples:
      | app              | page             |
      | client_manager   | client           |
      | devicemanager    | appbuildchannel  |
      | devicemanager    | appbuild         |
      | devicemanager    | devicegroup      |
      | devicemanager    | device           |
      | devicemanager    | mirrorserver     |
      | feedmanager      | category         |
      | feedmanager      | template         |
      | feedmanager      | imagefeed        |
      | feedmanager      | imagesnippet     |
      | feedmanager      | videofeed        |
      | feedmanager      | videosnippet     |
      | feedmanager      | webfeed          |
      | feedmanager      | websnippet       |
      | mediamanager     | calendarasset    |
      | mediamanager     | videoasset       |
      | mediamanager     | webasset         |
      | mediamanager     | webassettemplate |
      | mediamanager     | imageasset       |
      | mediamanager     | contentfeed      |
      | mediamanager     | playlist         |
      | schedule_manager | scheduledcontent |
      | schedule_manager | specialcontent   |
