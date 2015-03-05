Using step definitions from: steps/common_steps, steps/windows_steps, steps/lifecycle_steps, steps/scripting_steps
Feature: Windows server fast smoke test

    @ec2
    Scenario: Bootstraping
        Given I have a clean and stopped farm
        And I add role to this farm with winchef,storages
        When I start farm
        Then I see pending server M1
        And I wait and see running server M1
        And file 'C:\chef_result_file' exist in M1 windows
        And I have a M1 attached volume as V1
        And attached volume in M1 has size 1 Gb

    @ec2
    Scenario: Windows reboot
        When I reboot server M1
        Then Scalr receives Win_HostDown from M1
        And Scalr receives RebootFinish from M1
        And Scalr sends RebootFinish to M1
        And scalarizr is running on M1
        And scalr-upd-client is running on M1

    @ec2
    Scenario: Execute sync cmd script on Windows
        When I execute script 'Windows ping-pong. CMD' synchronous on M1
        Then I see script result in M1
        And script output contains 'pong' in M1

    @ec2
    Scenario: Execute async cmd script on Windows
        When I execute script 'Windows ping-pong. CMD' asynchronous on M1
        Then I see script result in M1
        And script output contains 'pong' in M1

    @ec2
    Scenario: Execute sync ps script on Windows
        When I execute script 'Windows ping-pong. PS' synchronous on M1
        Then I see script result in M1
        And script output contains 'pong' in M1

    @ec2
    Scenario: Execute async ps script on Windows
        When I execute script 'Windows ping-pong. PS' asynchronous on M1
        Then I see script result in M1
        And script output contains 'pong' in M1