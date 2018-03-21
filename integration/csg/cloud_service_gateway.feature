Feature: Check CSG
  In order to use CSG feature
  as a Scalr user
  I want to be able to manage cloud service access requests
  and CSG should work properly for AWS and Azure clouds
  and it works through proxy

  Scenario: Create and approve AWS service access request
    Given I have requested access to services on AWS as AR_AWS_1:
      | service             |
      | Api Gateway         |
      | Cognito Identity    |
      | Cognito User Pools  |
      | Device Farm         |
      | DynamoDb            |
      | Ecs                 |
      | Glacier             |
    And I see access request AR_AWS_1 in pending status on environment scope
    And I see access request AR_AWS_1 in pending status on account scope
    When I approve access request AR_AWS_1
    Then I see access request AR_AWS_1 in approved status on environment scope
    And I see access request AR_AWS_1 in approved status on account scope
    Then I obtain secret key for access request AR_AWS_1
    And I see access request AR_AWS_1 in active status on environment scope
    And I see access request AR_AWS_1 in active status on account scope

  Scenario: Create and approve another AWS service access request
    Given I have requested access to services on AWS as AR_AWS_2:
      | service             |
      | Lambda              |
      | Mobile              |
      | Pinpoint            |
      | Redshift            |
      | Route53             |
      | Ses                 |
      | Sns                 |
      | Sqs                 |
    And I see access request AR_AWS_2 in pending status on environment scope
    And I see access request AR_AWS_2 in pending status on account scope
    When I approve access request AR_AWS_2
    Then I see access request AR_AWS_2 in approved status on environment scope
    And I see access request AR_AWS_2 in approved status on account scope
    Then I obtain secret key for access request AR_AWS_2
    And I see access request AR_AWS_2 in active status on environment scope
    And I see access request AR_AWS_2 in active status on account scope

  Scenario: Create and deny AWS service access request
    Given I have requested access to services on AWS as AR_AWS_3:
      | service             |
      | Lambda              |
    And I see access request AR_AWS_3 in pending status on environment scope
    And I see access request AR_AWS_3 in pending status on account scope
    When I deny access request AR_AWS_3
    Then I see access request AR_AWS_3 in denied status on environment scope
    And I see access request AR_AWS_3 in denied status on account scope

  Scenario: Create and approve Azure service access request
    Given I have requested access to services on Azure as AR_AZ_1:
      | service             |
      | Container Registry  |
      | Container Service   |
      | Database            |
      | Event Hubs          |
    And I see access request AR_AZ_1 in pending status on environment scope
    And I see access request AR_AZ_1 in pending status on account scope
    When I approve access request AR_AZ_1
    Then I see access request AR_AZ_1 in approved status on environment scope
    And I see access request AR_AZ_1 in approved status on account scope
    Then I obtain secret key for access request AR_AZ_1
    And I see access request AR_AZ_1 in active status on environment scope
    And I see access request AR_AZ_1 in active status on account scope

  Scenario: Create and approve another Azure service access request
    Given I have requested access to services on Azure as AR_AZ_2:
      | service             |
      | Insights            |
      | Machine Learning    |
      | Stream Analytics    |
      | Web                 |
    And I see access request AR_AZ_2 in pending status on environment scope
    And I see access request AR_AZ_2 in pending status on account scope
    When I approve access request AR_AZ_2
    Then I see access request AR_AZ_2 in approved status on environment scope
    And I see access request AR_AZ_2 in approved status on account scope
    Then I obtain secret key for access request AR_AZ_2
    And I see access request AR_AZ_2 in active status on environment scope
    And I see access request AR_AZ_2 in active status on account scope

  Scenario: Create and deny Azure service access request
    Given I have requested access to services on Azure as AR_AZ_3:
      | service             |
      | Container Registry  |
    And I see access request AR_AZ_3 in pending status on environment scope
    And I see access request AR_AZ_3 in pending status on account scope
    When I deny access request AR_AZ_3
    Then I see access request AR_AZ_3 in denied status on environment scope
    And I see access request AR_AZ_3 in denied status on account scope

  Scenario Outline: Check approved access requests
    Then "<service>" service is <service_status> on <platform> using <request>
    And there are no errors in CSG log
    Examples:
      | request  | platform | service             | service_status |
      | AR_AWS_1 | AWS      | Api Gateway         | active         |
      | AR_AWS_1 | AWS      | Cognito Identity    | active         |
      | AR_AWS_1 | AWS      | Cognito User Pools  | active         |
      | AR_AWS_1 | AWS      | Device Farm         | active         |
      | AR_AWS_1 | AWS      | DynamoDb            | active         |
      | AR_AWS_1 | AWS      | Ecs                 | active         |
      | AR_AWS_1 | AWS      | Glacier             | active         |
      | AR_AWS_1 | AWS      | Lambda              | restricted     |
      | AR_AWS_1 | AWS      | Mobile              | restricted     |
      | AR_AWS_1 | AWS      | Pinpoint            | restricted     |
      | AR_AWS_1 | AWS      | Redshift            | restricted     |
      | AR_AWS_1 | AWS      | Route53             | restricted     |
      | AR_AWS_1 | AWS      | Ses                 | restricted     |
      | AR_AWS_1 | AWS      | Sns                 | restricted     |
      | AR_AWS_1 | AWS      | Sqs                 | restricted     |
      | AR_AWS_2 | AWS      | Api Gateway         | restricted     |
      | AR_AWS_2 | AWS      | Cognito Identity    | restricted     |
      | AR_AWS_2 | AWS      | Cognito User Pools  | restricted     |
      | AR_AWS_2 | AWS      | Device Farm         | restricted     |
      | AR_AWS_2 | AWS      | DynamoDb            | restricted     |
      | AR_AWS_2 | AWS      | Ecs                 | restricted     |
      | AR_AWS_2 | AWS      | Glacier             | restricted     |
      | AR_AWS_2 | AWS      | Lambda              | active         |
      | AR_AWS_2 | AWS      | Mobile              | active         |
      | AR_AWS_2 | AWS      | Pinpoint            | active         |
      | AR_AWS_2 | AWS      | Redshift            | active         |
      | AR_AWS_2 | AWS      | Route53             | active         |
      | AR_AWS_2 | AWS      | Ses                 | active         |
      | AR_AWS_2 | AWS      | Sns                 | active         |
      | AR_AWS_2 | AWS      | Sqs                 | active         |
      | AR_AZ_1  | Azure    | Container Registry  | active         |
      | AR_AZ_1  | Azure    | Container Service   | active         |
      | AR_AZ_1  | Azure    | Database            | active         |
      | AR_AZ_1  | Azure    | Event Hubs          | active         |
      | AR_AZ_1  | Azure    | Insights            | restricted     |
      | AR_AZ_1  | Azure    | Machine Learning    | restricted     |
      | AR_AZ_1  | Azure    | Stream Analytics    | restricted     |
      | AR_AZ_1  | Azure    | Web                 | restricted     |
      | AR_AZ_2  | Azure    | Container Registry  | restricted     |
      | AR_AZ_2  | Azure    | Container Service   | restricted     |
      | AR_AZ_2  | Azure    | Database            | restricted     |
      | AR_AZ_2  | Azure    | Event Hubs          | restricted     |
      | AR_AZ_2  | Azure    | Insights            | active         |
      | AR_AZ_2  | Azure    | Machine Learning    | active         |
      | AR_AZ_2  | Azure    | Stream Analytics    | active         |
      | AR_AZ_2  | Azure    | Web                 | active         |

  Scenario: Revoke AWS service access request
    Given I have active access request AR_AWS_1
    When I revoke access request AR_AWS_1
    Then I see access request AR_AWS_1 in revoked status on environment scope
    And I see access request AR_AWS_1 in revoked status on account scope

  Scenario: Archive another AWS service access request
    Given I have active access request AR_AWS_2
    When I archive access request AR_AWS_2
    Then I see access request AR_AWS_2 in archived status on environment scope
    And I see access request AR_AWS_2 in archived status on account scope

  Scenario: Revoke Azure service access request
    Given I have active access request AR_AZ_1
    When I revoke access request AR_AZ_1
    Then I see access request AR_AZ_1 in revoked status on environment scope
    And I see access request AR_AZ_1 in revoked status on account scope

  Scenario: Archive another Azure service access request
    Given I have active access request AR_AZ_2
    When I archive access request AR_AZ_2
    Then I see access request AR_AZ_2 in archived status on environment scope
    And I see access request AR_AZ_2 in archived status on account scope

  Scenario Outline: Check revoked and archived access requests
    Then "<service>" service is <service_status> on <platform> using <request>
    And there are no errors in CSG log
    Examples:
      | request  | platform | service             | service_status |
      | AR_AWS_1 | AWS      | Api Gateway         | disabled       |
      | AR_AWS_1 | AWS      | Cognito Identity    | disabled       |
      | AR_AWS_1 | AWS      | Cognito User Pools  | disabled       |
      | AR_AWS_1 | AWS      | Device Farm         | disabled       |
      | AR_AWS_1 | AWS      | DynamoDb            | disabled       |
      | AR_AWS_1 | AWS      | Ecs                 | disabled       |
      | AR_AWS_1 | AWS      | Glacier             | disabled       |
      | AR_AWS_1 | AWS      | Lambda              | disabled       |
      | AR_AWS_1 | AWS      | Mobile              | disabled       |
      | AR_AWS_1 | AWS      | Pinpoint            | disabled       |
      | AR_AWS_1 | AWS      | Redshift            | disabled       |
      | AR_AWS_1 | AWS      | Route53             | disabled       |
      | AR_AWS_1 | AWS      | Ses                 | disabled       |
      | AR_AWS_1 | AWS      | Sns                 | disabled       |
      | AR_AWS_1 | AWS      | Sqs                 | disabled       |
      | AR_AWS_2 | AWS      | Api Gateway         | disabled       |
      | AR_AWS_2 | AWS      | Cognito Identity    | disabled       |
      | AR_AWS_2 | AWS      | Cognito User Pools  | disabled       |
      | AR_AWS_2 | AWS      | Device Farm         | disabled       |
      | AR_AWS_2 | AWS      | DynamoDb            | disabled       |
      | AR_AWS_2 | AWS      | Ecs                 | disabled       |
      | AR_AWS_2 | AWS      | Glacier             | disabled       |
      | AR_AWS_2 | AWS      | Lambda              | disabled       |
      | AR_AWS_2 | AWS      | Mobile              | disabled       |
      | AR_AWS_2 | AWS      | Pinpoint            | disabled       |
      | AR_AWS_2 | AWS      | Redshift            | disabled       |
      | AR_AWS_2 | AWS      | Route53             | disabled       |
      | AR_AWS_2 | AWS      | Ses                 | disabled       |
      | AR_AWS_2 | AWS      | Sns                 | disabled       |
      | AR_AWS_2 | AWS      | Sqs                 | disabled       |
      | AR_AZ_1  | Azure    | Container Registry  | disabled       |
      | AR_AZ_1  | Azure    | Container Service   | disabled       |
      | AR_AZ_1  | Azure    | Database            | disabled       |
      | AR_AZ_1  | Azure    | Event Hubs          | disabled       |
      | AR_AZ_1  | Azure    | Insights            | disabled       |
      | AR_AZ_1  | Azure    | Machine Learning    | disabled       |
      | AR_AZ_1  | Azure    | Stream Analytics    | disabled       |
      | AR_AZ_1  | Azure    | Web                 | disabled       |
      | AR_AZ_2  | Azure    | Container Registry  | disabled       |
      | AR_AZ_2  | Azure    | Container Service   | disabled       |
      | AR_AZ_2  | Azure    | Database            | disabled       |
      | AR_AZ_2  | Azure    | Event Hubs          | disabled       |
      | AR_AZ_2  | Azure    | Insights            | disabled       |
      | AR_AZ_2  | Azure    | Machine Learning    | disabled       |
      | AR_AZ_2  | Azure    | Stream Analytics    | disabled       |
      | AR_AZ_2  | Azure    | Web                 | disabled       |

  Scenario: Configure proxy server
    Given I have configured revizor environment:
      | name           | value          |
      | platform       | gce            |
      | dist           | ubuntu1404     |
    And I have a clean and stopped farm
    And I add role to this farm
    When I start farm
    Then I expect server bootstrapping as P1
    And I execute script 'Launch mitmproxy' synchronous on P1
    And I set proxy for AWS,Azure in Scalr to P1
    And I restart service "cloud-service-gateway"

  Scenario: Create and approve service access requests for proxy check
    Given I have requested access to services on AWS as AR_AWS_P:
      | service             |
      | Api Gateway         |
      | Cognito Identity    |
      | Cognito User Pools  |
      | Device Farm         |
      | DynamoDb            |
      | Ecs                 |
      | Glacier             |
      | Lambda              |
      | Mobile              |
      | Pinpoint            |
      | Redshift            |
      | Route53             |
      | Ses                 |
      | Sns                 |
      | Sqs                 |
    And I have requested access to services on Azure as AR_AZ_P:
      | service             |
      | Container Registry  |
      | Container Service   |
      | Database            |
      | Event Hubs          |
      | Insights            |
      | Machine Learning    |
      | Stream Analytics    |
      | Web                 |
    Then I approve access request AR_AWS_P
    And I approve access request AR_AZ_P
    And I obtain secret key for access request AR_AWS_P
    And I obtain secret key for access request AR_AZ_P

  Scenario Outline: Check approved services via proxy
    Given I have active access request <request>
    Then "<service>" service is active on <platform> using <request>
    And requests to "<service>" on <platform> are present in last proxy logs on P1
    And there are no errors in CSG log
    Examples:
      | request  | platform  | service             |
      | AR_AWS_P | AWS       | Api Gateway         |
      | AR_AWS_P | AWS       | Cognito Identity    |
      | AR_AWS_P | AWS       | Cognito User Pools  |
      | AR_AWS_P | AWS       | Device Farm         |
      | AR_AWS_P | AWS       | DynamoDb            |
      | AR_AWS_P | AWS       | Ecs                 |
      | AR_AWS_P | AWS       | Glacier             |
      | AR_AWS_P | AWS       | Lambda              |
      | AR_AWS_P | AWS       | Mobile              |
      | AR_AWS_P | AWS       | Pinpoint            |
      | AR_AWS_P | AWS       | Redshift            |
      | AR_AWS_P | AWS       | Route53             |
      | AR_AWS_P | AWS       | Ses                 |
      | AR_AWS_P | AWS       | Sns                 |
      | AR_AWS_P | AWS       | Sqs                 |
      | AR_AZ_P  | Azure     | Container Registry  |
      | AR_AZ_P  | Azure     | Container Service   |
      | AR_AZ_P  | Azure     | Database            |
      | AR_AZ_P  | Azure     | Event Hubs          |
      | AR_AZ_P  | Azure     | Insights            |
      | AR_AZ_P  | Azure     | Machine Learning    |
      | AR_AZ_P  | Azure     | Stream Analytics    |
      | AR_AZ_P  | Azure     | Web                 |
