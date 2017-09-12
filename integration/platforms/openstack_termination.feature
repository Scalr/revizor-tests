Feature: Check Openstack termination strategy on failed server
    Verify openstack termination policy work fine if server in Failed state on cloud.
    Issue: HSV-107
    TODO: Add feature for missing_server

    Scenario: Bootstrapping server
        Given I have configured revizor environment:
          | name       | value     |
          | platform   | openstack |
        Given I have a clean and stopped farm
        And I add role to this farm
        When I start farm
        And I expect server bootstrapping as M1
        And save system log status for server M1
        And Scalr file "StatusAdapter.php" modified for test

    Scenario: Verify action_on_failed_server = "ignore"
        Given I have configured scalr config:
          | name                                    | value  |
          | scalr.openstack.action_on_failed_server | ignore |
        Then I restart service "zmq_service"
        And server M1 hasn't changed its status in 5 minutes
        And system log hasn't new messages for server M1

    Scenario: Verify action_on_failed_server = "alert"
        Given I have configured scalr config:
            | name                                    | value  |
            | scalr.openstack.action_on_failed_server | alert  |
        Then I restart service "zmq_service"
        And server M1 hasn't changed its status in 5 minutes
        And system log has new message with body '(Platform: openstack) was failed. Status: ACTIVE.' for server M1

    Scenario: Verify action_on_failed_server not exist
        Given I have configured scalr config:
            | name                                    | value     |
            | scalr.openstack.action_on_failed_server | terminate |
        Then I restart service "zmq_service"
        When I wait server M1 in terminated state
        And system log has new message with body '(Platform: openstack) was terminated in cloud or from within an OS. Status: ACTIVE.' for server M1
        Then I see pending server M2