Using step definitions from: steps/common_steps, steps/windows_steps, steps/lifecycle_steps, steps/scripting_steps
Feature: Windows server lifecycle
    In order to manage server lifecycle
    As a scalr user
    I want to be able to monitor server state changes

    @ec2
    Scenario: Bootstraping
        Given I have a clean and stopped farm
        And I add role to this farm with winchef
        When I start farm
        Then I see pending server M1
        And I wait and see initializing server M1
        And I wait and see running server M1
        And file 'C:\chef_result_file' exist in M1 windows

    @ec2
    Scenario: Restart scalarizr
        Given I have running server M1
        When I reboot windows scalarizr in M1
        And see 'Scalarizr terminated' in M1 windows log
        And scalarizr is running on M1
        And not ERROR in M1 scalarizr windows log

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
        And last script output contains 'pong' in M1

    @ec2
    Scenario: Execute async cmd script on Windows
        When I execute script 'Windows ping-pong. CMD' asynchronous on M1
        Then I see script result in M1
        And last script output contains 'pong' in M1

    @ec2
    Scenario: Execute sync ps script on Windows
        When I execute script 'Windows ping-pong. PS' synchronous on M1
        Then I see script result in M1
        And last script output contains 'pong' in M1

    @ec2
    Scenario: Execute async ps script on Windows
        When I execute script 'Windows ping-pong. PS' asynchronous on M1
        Then I see script result in M1
        And last script output contains 'pong' in M1

    @ec2
    Scenario: Restart farm
        When I stop farm
        And wait all servers are terminated
        Then I start farm
        And I expect server bootstrapping as M1
        And file 'c:/chef_result_file' exist in M1 windows