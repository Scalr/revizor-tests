Using step definitions from: steps/common_steps, steps/lifecycle_steps, steps/scripting_steps, steps/pkg_update_steps, steps/import_steps, steps/discovery_manager_steps
Feature: Discovery manager service
    In order to manage non Scalr resources
    As a scalr user
    I use Discovery manager service

    @ec2 @agentless
    Scenario: Import running instances into Scalr
        Given I have a an empty running farm
        When I have a server running in cloud
        Then I get an image from the server running in the cloud
        And I add image to the new role as non scalarized
        And I add created role to the farm with custom deploy options
        And I run the server imports running in the cloud

    @ec2 @agentless
    Scenario: Deploy scalr agent
        Given I see running server M1
        And scalarizr not installed on the M1 server
        Then I install scalarizr to the server M1
        When I trigger the deploy and run scalr agent on the M1 server
        Then connection with agent on the M1 server was established
        And scalarizr version is last in M1
        When I reboot server M1
        And Scalr receives RebootFinish from M1
        When I execute script 'Linux ping-pong' synchronous on M1
        Then I see script result in M1
        And script output contains 'pong' in M1
