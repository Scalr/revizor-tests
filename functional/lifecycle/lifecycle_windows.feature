Using step definitions from: steps/common_steps, steps/windows_steps, steps/lifecycle_steps, steps/scripting_steps
Feature: Windows server lifecycle
    In order to manage server lifecycle
    As a scalr user
    I want to be able to monitor server state changes

    @ec2 @gce
    Scenario: Bootstraping
        Given I have a clean and stopped farm
        And I add role to this farm with winchef,storages
        When I start farm
        Then I see pending server M1
        And I wait and see running server M1
        And file 'C:\chef_result_file' exist in M1 windows
        And server M1 has disks E: 1 Gb, D: 2 Gb, Z(test_label): 4 Gb
        And I have a M1 attached volume as V1
        And attached volume V1 has size 1 Gb
        And hostname in M1 is valid

    @ec2 @gce
    Scenario: Restart scalarizr
        Given I have running server M1
        When I reboot windows scalarizr in M1
        And see 'Scalarizr terminated' in M1 windows log
        And scalarizr is running on M1
        And not ERROR in M1 scalarizr windows log

    @ec2 @gce
    Scenario: Windows reboot
        When I reboot server M1
        Then Scalr receives Win_HostDown from M1
        And Scalr receives RebootFinish from M1
        And Scalr sends RebootFinish to M1
        And scalarizr is running on M1
        And scalr-upd-client is running on M1

    @ec2 @gce
    Scenario: Execute sync cmd script on Windows
        When I execute script 'Windows ping-pong. CMD' synchronous on M1
        Then I see script result in M1
        And script output contains 'pong' in M1

    @ec2 @gce
    Scenario: Execute async cmd script on Windows
        When I execute script 'Windows ping-pong. CMD' asynchronous on M1
        Then I see script result in M1
        And script output contains 'pong' in M1

    @ec2 @gce
    Scenario: Execute sync ps script on Windows
        When I execute script 'Windows ping-pong. PS' synchronous on M1
        Then I see script result in M1
        And script output contains 'pong' in M1

    @ec2 @gce
    Scenario: Execute async ps script on Windows
        When I execute script 'Windows ping-pong. PS' asynchronous on M1
        Then I see script result in M1
        And script output contains 'pong' in M1

    @ec2 @gce
    Scenario: Execute sync ps script on Windows from URL
        When I execute local script 'https://gist.githubusercontent.com/gigimon/d233b77be7c04480c01a/raw/cd05c859209e1ff23961a371e0e2298ab3fb0257/gistfile1.txt' asynchronous on M1
        Then I see script result in M1
        And script output contains 'Script runned from URL' in M1

    @ec2 @gce
    Scenario: Restart farm
        When I stop farm
        And wait all servers are terminated
        Then I start farm
        And I expect server bootstrapping as M1
        And file 'C:\chef_result_file' exist in M1 windows

    @ec2 @gce
    Scenario: Reboot on bootstrapping
        Given I have a clean and stopped farm
        And I add role to this farm with init_reboot,small_win_orchestration
        When I start farm
        And I see pending server M1
        When I wait server M1 in initializing state
        Then I wait server M1 in running state
        And hostname in M1 is valid

    @ec2 @gce
    Scenario: Bootstraping with failed hostname
        Given I have a clean and stopped farm
        And I add role to this farm with failed_hostname
        When I start farm
        And I see pending server M1
        And I wait server M1 in failed state