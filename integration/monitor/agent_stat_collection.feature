Feature: Check monitor pulling/pushing mechanism

  Scenario: Check Pulling mechanism
    Given I have a an empty running farm
    And I configure roles in testenv:
      | server_index   | platform  |    dist    |  branch  |  ci_repo  |
      | S1             | gce       | ubuntu1404 |  5.10.0  |  snapshot |
      | S2             | gce       |   centos7  |  5.10.0  |  snapshot |
      | S3             | gce       |   win2012  |  5.10.0  |  snapshot |
    Then I wait server S1,S2,S3 in running state
    And not ERROR in S1,S2,S3 scalarizr log
    And Scalr services are in RUNNING state
    And agent stat for S1,S2,S3 is collected via Pulling
    And data for S1,S2,S3 is present in influx
    And no "Traceback" in service "monitor" log

  Scenario: Check Pushing mechanism
    Given I have a an empty running farm
    And I configure roles in testenv:
      | server_index   | platform  |    dist    |  branch  |  ci_repo  |
      | S1             | gce       | ubuntu1404 |  master  |  drone    |
      | S2             | gce       |   centos7  |  master  |  drone    |
      | S3             | gce       |   win2012  |  master  |  drone    |
    Then I wait server S1,S2,S3 in running state
    And not ERROR in S1,S2,S3 scalarizr log
    And Scalr services are in RUNNING state
    And agent stat for S1,S2,S3 is collected via Pushing
    And data for S1,S2,S3 is present in influx
    And no "Traceback" in service "monitor" log

  # Scenario: Configure proxy server
  #   Given I have configured revizor environment:
  #     | name           | value          |
  #     | platform       | gce            |
  #     | dist           | ubuntu1404     |
  #     | branch         | master         |
  #   And I have a clean and stopped farm
  #   And I add role to this farm
  #   When I start farm
  #   Then I expect server bootstrapping as P1
  #   And I execute local script 'https://git.io/vA52O' synchronous on P1
  #   And I set proxy for AWS in Scalr to P1
  #   And I restart service "monitor"
  #   And I configure roles in testenv:
  #     | server_index   | platform  |    dist    |  branch  |  ci_repo  |
  #     | S1             | ec2       | ubuntu1404 |  5.10.0  |  snapshot |
  #     | S2             | ec2       | ubuntu1404 |  master  |  drone    |
  #   Then I wait server S1,S2 in running state
  #   And not ERROR in S1,S2 scalarizr log
  #   And Scalr services are in RUNNING state
  #   And agent stat for S1 is collected via Pulling
  #   And agent stat for S2 is collected via Pushing
  #   And proxy P1 log contains message "CONNECT ec2.us-east-1.amazonaws.com:443 testuser"
