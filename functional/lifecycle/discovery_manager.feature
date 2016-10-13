Using step definitions from: steps/common_steps, steps/lifecycle_steps, steps/scripting_steps, steps/pkg_update_steps, steps/import_steps
Feature: Discovery manager service
    In order to manage non Scalr resources
    As a scalr user
    I use Discovery manager service

    @ec2 @rackspaceng @openstack @agentless
    Scenario: Import running instances into scalr
        Given I have a server running in cloud
        Then I install scalarizr to the server
        Given I have a an empty running farm
        And I add image to the new role
        And I add created role to the farm
        Then I trigger the import and deploy scalr agent
        When I see running server M1
        And scalarizr version is last in M1
        Then I reboot hard server M1
        When I expect server bootstrapping as M1
        Then I execute script 'Linux ping-pong' synchronous on M1
        And I see script result in M1
        And script output contains 'pong' in M1
