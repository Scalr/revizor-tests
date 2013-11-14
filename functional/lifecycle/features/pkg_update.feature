Feature: Update scalarizr test

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstraping
        Given I have a an empty running farm
        When I add role to this farm
        When I start farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Change repo
        When I change repo in M1 to system
        And pin system repo in M1
        And update scalarizr in M1
        And scalarizr version is last in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Restart scalarizr after update
        When I reboot scalarizr in M1
        And see 'Scalarizr terminated' in M1 log
        Then scalarizr process is 2 in M1
        And not ERROR in M1 scalarizr log