Using step definitions from: steps/common_steps, steps/lifecycle_steps, steps/scripting_steps, steps/szradm_steps
Feature: Linux server lifecycle in Azure
    In order to manage server lifecycle
    As a scalr user
    I want to be able to monitor server state changes

    @azure
    Scenario: Bootstraping
        Given I have a clean and stopped farm
        And I add role to this farm
        When I start farm
        Then I see pending server M1
        And I wait and see running server M1
        And scalarizr version is last in M1

    @azure
    Scenario: Linux reboot
        Given I have running server M1
        When I reboot server M1
        And Scalr receives RebootFinish from M1

    @azure
    Scenario: Execute script on Linux
        Given I have running server M1
        When I execute script 'Linux ping-pong' synchronous on M1
        And I see script result in M1
        And script output contains 'pong' in M1

    @azure
    Scenario: Execute non-ascii script on Linux
        Given I have running server M1
        When I execute script 'Non ascii script' synchronous on M1
        Then I see script result in M1
        And script output contains 'Non_ascii_script' in M1

    @azure
    Scenario: Restart scalarizr
        Given I have running server M1
        When I reboot scalarizr in M1
        And see 'Scalarizr terminated' in M1 log
        And not ERROR in M1 scalarizr log

    @azure
    Scenario: Stop farm
        When I stop farm
        And wait all servers are terminated

    @azure
    Scenario: Start farm
        When I start farm with delay
        Then I expect server bootstrapping as M1
        And scalarizr version from system repo is last in M1
