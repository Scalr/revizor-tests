Using step definitions from: steps/common_steps, steps/new_szr_upd_system, steps/scripting_steps
Feature: New scalarizr update system test

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstraping
        Given I have a an empty running farm
        When I add role to this farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Change repo
        When I change repo in M1
        And pin repo in M1
        Then update scalarizr in M1
        And scalarizr version is last in M1
        Then scalarizr is running on M1
        And scalr-upd-client is running on M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Restart scalarizr after update
        When I reboot scalarizr in M1
        And see 'Scalarizr terminated' in M1 log
        And not ERROR in M1 scalarizr log
        Then scalarizr is running on M1
        And scalr-upd-client is running on M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Execute 1 sync and 1 async scripts
        When I execute script 'Linux ping-pong' synchronous on M1
        And I see script result in M1
        Then I execute script 'Linux ping-pong' asynchronous on M1
        And I see script result in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Execute restart scalarizr
        When I execute script 'Restart scalarizr' synchronous on M1
        And I see script result in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify server bootstrap with new update system
        When I change branch for role
        Then I start a new server for role
        And I expect server bootstrapping as M2
        And scalarizr version is last in M2
        Then scalarizr is running on M2
        And scalr-upd-client is running on M2