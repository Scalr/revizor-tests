Feature: Check CSG
  In order to use CSG feature
  as a Scalr user
  I want to be able to manage cloud service access requests
  and CSG should work properly for AWS and Azure clouds
  and it works through proxy

  Scenario: Create and approve cloud service access request
    Given I have requested access to services on AWS as AR1
      | service         |
      | Lambda          |
      | ECS             |
    And I see access request AR1 in pending status on environment scope
    And I see access request AR1 in pending status on account scope
    When I approve access request AR1
    Then I see access request AR1 in approved status on environment scope
    And I see access request AR1 in approved status on account scope
    Then I obtain secret key for access request AR1
    And I see access request AR1 in active status on environment scope
    And I see access request AR1 in active status on account scope
