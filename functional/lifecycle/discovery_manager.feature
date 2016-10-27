Using step definitions from: steps/common_steps, steps/lifecycle_steps, steps/scripting_steps, steps/pkg_update_steps, steps/import_steps
Feature: Discovery manager service
    In order to manage non Scalr resources
    As a scalr user
    I use Discovery manager service

    @ec2 @gce @agentless
    Scenario: Bootstraping
        Given I have a server running in cloud
        And I have a clean and stopped farm
        When I have a clean image
        Then I add image to the new role as non scalarized
        And I add created role to the farm
        And I start farm

    @ec2 @gce @agentless
    Scenario: Import running instances into scalr
        Given I run the server imports running in the cloud
        When I see running server M1
        Then I install scalarizr to the server M1
        Then I trigger the deploy scalr agent
        When scalarizr version is last in M1
        Then I reboot server M1
        When I expect server bootstrapping as M1
        Then I execute script 'Linux ping-pong' synchronous on M1
        And I see script result in M1
        And script output contains 'pong' in M1
