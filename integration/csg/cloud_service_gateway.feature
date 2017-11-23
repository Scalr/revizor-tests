Feature: Check CSG
    In order to use CSG feature
    as a Scalr user
    I want to be able to manage cloud service access requests
    and CSG should work properly for AWS and Azure clouds
    and it works through proxy

    Scenario: Create and approve cloud service access request
        Given I have requested access to services on AWS as AR1:
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

    Scenario: Check approved services read access
        Given I have active access request AR1
        When I execute "list-functions" for Lambda service on AWS using AR1
        Then the response contains no errors

    Scenario: Check not authorized service access
        Given I have active access request AR1
        When I execute "list-reusable-delegation-sets" for Route53 service on AWS using AR1
        Then the response contains access error

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

    Scenario: Check approved services access via proxy
        Given I have active access request AR1
        When I execute "list-functions" for Lambda service on AWS using AR1
        Then the response contains no errors
        And last proxy logs on P1 contain "lambda.us-east-1.amazonaws.com"
