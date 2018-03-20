Feature: Check docker policy and scalr-authz plugin

  Scenario: Prepare env
    Given I have configured revizor environment:
      | name           | value          |
      | platform       | gce            |
      | dist           | ubuntu1404     |
    And I have a clean and stopped farm

  Scenario: No policy, no docker
    When I add role to this farm
    And I start farm
    Then I expect server bootstrapping as D1
    And docker-authz plugin is not installed on D1

  Scenario: No policy, docker installed after running
    Given I execute local script 'https://get.docker.com' synchronous on D1
    And I reboot scalarizr in D1
    Then docker-authz plugin is not installed on D1
    And all policies do not work on D1

  Scenario: Docker installed after running, policy configured after running, scalarizr restarted
    Given I add new Container policy group 'rev-docker-1' as P1
    And I link policy group P1 to environment 'acc1env1'
    When I reboot scalarizr in D1
    Then docker-authz plugin is not installed on D1

  Scenario: Policy configured, no docker
    Given I stop farm
    When I start farm
    Then I expect server bootstrapping as D2
    And docker-authz plugin is not installed on D2

  Scenario: Policy configured, docker installed after running, scalarizr restarted
    Given I execute local script 'https://get.docker.com' synchronous on D2
    And I reboot scalarizr in D2
    Then docker-authz plugin is not installed on D2
    And all policies do not work on D2

  Scenario: Policy configured, docker installed after running, policy changed, scalarizr restarted
    Given I unlink policy group P1 from environment 'acc1env1'
    And I delete policy group P1
    Then I add new Container policy group 'rev-docker-2' as P2
    And I link policy group P2 to environment 'acc1env1'
    And I reboot scalarizr in D2
    Then docker-authz plugin is not installed on D2

  Scenario: No policy, docker installed
    Given I unlink policy group P2 from environment 'acc1env1'
    And I delete policy group P2
    And I delete base role from this farm
    And I add role to this farm with docker
    Then I expect server bootstrapping as D3
    And docker-authz plugin is not installed on D3
    And all policies do not work on D3

  Scenario: No policy, docker installed, scalarizr restarted
    When I reboot scalarizr in D3
    Then docker-authz plugin is not installed on D3

  Scenario: Docker installed, policy configured after running, scalarizr restarted
    Given I add new Container policy group 'rev-docker-3' as P3
    And I link policy group P3 to environment 'acc1env1'
    When I reboot scalarizr in D3
    Then docker-authz plugin is not installed on D3
    And all policies do not work on D3

  Scenario: Policy configured, docker installed
    Given I stop farm
    When I start farm
    Then I expect server bootstrapping as D4
    And docker-authz plugin is installed on D4
    And all policies work on D4

  Scenario: Policy configured, docker installed, server rebooted
    Given I reboot server D4
    And Scalr receives RebootFinish from D4
    Then docker-authz plugin is installed on D4
    And all policies work on D4

  Scenario: Policy configured, docker installed, policy removed, server rebooted
    Given I unlink policy group P3 from environment 'acc1env1'
    And I delete policy group P3
    And I reboot server D4
    And Scalr receives RebootFinish from D4
    Then docker-authz plugin is installed on D4
    And all policies work on D4

  Scenario: Policy configured, docker installed, policy changed, server rebooted
    Given I add new Container policy group 'rev-docker-4' with ports,mounts as P4
    And I link policy group P4 to environment 'acc1env1'
    And I reboot server D4
    And Scalr receives RebootFinish from D4
    Then docker-authz plugin is installed on D4
    And all policies work on D4

  Scenario: Policy configured, docker installed, policy changed, new instance launched
    Given I stop farm
    When I start farm
    Then I expect server bootstrapping as D5
    And docker-authz plugin is installed on D5
    And ports,mounts policies work on D5
    And escalating,privileged,sources policies do not work on D5

  Scenario: Policy configured, windows instance is launched
    Given I delete base role from this farm
    And I have configured revizor environment:
      | name           | value          |
      | dist           | win2012        |
    And I add role to this farm
    Then I expect server bootstrapping as W1
