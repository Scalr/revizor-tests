Using step definitions from: steps/common_steps, steps/lifecycle_steps, steps/scripting_steps, steps/szradm_steps
Feature: Run new server in role and wait bootstrapping

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @azure
    Scenario: Bootstraping
        Given I have a clean and stopped farm
        And I add role to this farm
        When I start farm
        Then I see pending server M1
        And I wait and see running server M1
        And scalarizr version is last in M1