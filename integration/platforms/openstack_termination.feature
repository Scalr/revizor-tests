Feature: Check Openstack termination strategy on failed server
    Verify openstack termination policy work fine if server in Failed state on cloud.
    Issue: HSV-107
    TODO: Add feature for missing_server

    Scenario: Bootstrapping server
        Given I have configured revizor environment:
          | name       | value     |
          | platform   | openstack |
#        Given I have a clean and stopped farm
#        And I add role to this farm
#        When I start farm
#        And I expect server bootstrapping as M1
        And Scalr file "StatusAdapter.php" modified for test

    Scenario: Verify action_on_missing_server = "ignore"
        Given I have configured scalr config:
          | name                                    | value  |
          | scalr.openstack.action_on_failed_server | ignore |
        Then I restart service "zmq_service"
#        And server M1 not change status for 5 minutes
#        And system log hasn't messages for server M1
#
    Scenario: Verify action_on_missing_server = "alert"
        Given I have configured scalr config:
            | name                                    | value  |
            | scalr.openstack.action_on_failed_server | alert  |
        Then I restart service "zmq_service"
#        And server M1 not change status for 5 minutes
#        And system log has message for server M1
#
    Scenario: Verify action_on_missing_server not exist
        Given I have configured scalr config:
            | name                                    | value     |
            | scalr.openstack.action_on_failed_server | terminate |
        Then I restart service "zmq_service"
        When I wait and see terminated server M1
        Then I see pending server M2