Feature: Check CSG
  In order to use CSG feature
  as a Scalr user
  I want to be able to manage cloud service access requests
  and CSG should work properly for AWS and Azure clouds
  and it works through proxy

  Scenario: Create and approve AWS service access request
    Given I have requested access to services on AWS as AR1:
      | service |
      | Lambda  |
    And I see access request AR1 in pending status on environment scope
    And I see access request AR1 in pending status on account scope
    When I approve access request AR1
    Then I see access request AR1 in approved status on environment scope
    And I see access request AR1 in approved status on account scope
    Then I obtain secret key for access request AR1
    And I see access request AR1 in active status on environment scope
    And I see access request AR1 in active status on account scope

  Scenario: Create and approve Azure service access request
    Given I have requested access to services on Azure as AR2:
      | service |
      | Web     |
    And I see access request AR2 in pending status on environment scope
    And I see access request AR2 in pending status on account scope
    When I approve access request AR2
    Then I see access request AR2 in approved status on environment scope
    And I see access request AR2 in approved status on account scope
    Then I obtain secret key for access request AR2
    And I see access request AR2 in active status on environment scope
    And I see access request AR2 in active status on account scope

  Scenario Outline: Check approved services
    Given I have active access request <request>
    Then <service> service works on <platform> using <request>
    Examples:
      | request  | platform  | service   |
      | AR1      | AWS       | Lambda    |
      | AR2      | Azure     | Web       |

  Scenario: Configure proxy server
    Given I have configured revizor environment:
      | name           | value          |
      | platform       | gce            |
      | dist           | ubuntu1404     |
    And I have a clean and stopped farm
    And I add role to this farm
    When I start farm
    Then I expect server bootstrapping as P1
    And I execute local script 'https://git.io/vFb0z' synchronous on P1
    And I set proxy for AWS,Azure in Scalr to P1
    And I restart service "cloud-service-gateway"

  Scenario Outline: Check approved services via proxy
    Given I have active access request <request>
    Then <service> service works on <platform> using <request>
    And requests to <service> on <platform> are present in last proxy logs on P1
    Examples:
      | request  | platform  | service   |
      | AR1      | AWS       | Lambda    |
      | AR2      | Azure     | Web       |
