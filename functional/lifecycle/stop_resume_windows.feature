Using step definitions from: steps/common_steps, steps/lifecycle_steps, steps/chef_boot_steps, steps/windows_steps
Feature: Windows server resume strategy
    In order to check resume strategy
    I monitoring server state changes

    @ec2 @gce @cloudstack @boot
    Scenario: Bootstraping
        Given I have a clean and stopped farm
        And I add role to this farm with winchef,termination_preferences
        When I start farm
        Then I see pending server M1
        And I wait and see running server M1
        Then I check file 'C:\chef_result_file' exist on M1 windows
        And I remove file 'C:\chef_result_file' from M1 windows

    @ec2 @gce @cloudstack @stopresume
    Scenario: Stop/resume
        When I suspend server M1
        Then BeforeHostTerminate (Suspend) event was fired by M1
        And Scalr sends BeforeHostTerminate to M1
        Then I wait server M1 in suspended state
        And HostDown (Suspend) event was fired by M1
        And Server M1 exists on chef nodes list
        #And Scalr receives Win_HostDown from M1
        Then I wait and see new running server M2
        When I resume server M1
        Then I wait server M1 in resuming state
        And I wait server M1 in running state
        Then Scalr receives RebootFinish from M1
        And ResumeComplete event was fired by M1
        Then I wait server M1 in running state
        And HostInit,BeforeHostUp events were not fired after M1 resume
        Then I check file 'C:\chef_result_file' not exist on M1 windows

    @ec2 @gce @cloudstack
    Scenario: Verify Scalr delete chef nodes
        When I stop farm
        And wait all servers are terminated
        And Server M1 not exists on chef nodes list

    @ec2 @gce @cloudstack @stopresume @suspend
    Scenario: FarmSuspend
        Given I have a clean and stopped farm
        And I add base role to this farm
        When I start farm
        Then I expect server bootstrapping as M1
        When I suspend farm
        Then I wait farm in suspended state
        Then BeforeHostTerminate (Suspend) event was fired by M1
        And Scalr sends BeforeHostTerminate to M1
        Then I wait server M1 in suspended state
        And HostDown (Suspend) event was fired by M1
        And I wait 1 minutes
        And wait all servers are suspended
