Using step definitions from: steps/scaling_steps
Feature: Windows server read/execute scaling test

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus
    Scenario: Bootstraping execute scaling
        Given I have a clean and stopped farm
        And I add role to this farm with prepare_scaling_win,scaling_execute_win
        When I start farm
        Then I expect server bootstrapping as M1
        And scalarizr version from system repo is last in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus
    Scenario: Test execute scaling up
        When I set file 'C:\read_scaling.txt' content to 100 on M1
        Then I expect server bootstrapping as M2
        And I set file 'C:\read_scaling.txt' content to 60 on M1
        And not ERROR in M1 scalarizr log
        And not ERROR in M2 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus
    Scenario: Test execute scaling down
        When I set file 'C:\read_scaling.txt' content to 0 on M1
        Then I wait server M2 in terminated state
        And not ERROR in M1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus
    Scenario: Bootstraping read scaling
        Given I have a clean and stopped farm
        And I add role to this farm with scaling_read_win
        When I start farm
        Then I expect server bootstrapping as M1
        And scalarizr version from system repo is last in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus
    Scenario: Test read scaling up
        When I set file 'C:\read_scaling.txt' content to 100 on M1
        Then I expect server bootstrapping as M2
        And I set file 'C:\read_scaling.txt' content to 60 on M1
        And not ERROR in M1 scalarizr log
        And not ERROR in M2 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus
    Scenario: Test read scaling down
        When I set file 'C:\read_scaling.txt' content to 0 on M1
        Then I wait server M2 in terminated state
        And not ERROR in M1 scalarizr log