Using step definitions from: steps/common_steps, steps/lifecycle_steps, steps/scripting_steps
Feature: Linux server lifecycle
    In order to manage server lifecycle
    As a scalr user
    I want to be able to monitor server state changes

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @boot
    Scenario: Bootstraping
        Given I have a clean and stopped farm
        And I add role to this farm with deploy,storages
        When I start farm
        Then I see pending server M1
        And I wait and see running server M1
        And scalarizr version from system repo is last in M1
        Then Scalr receives DeployResult from M1
        And directory '/var/www/src' exist in M1
        And hostname in M1 is valid

    @ec2 @openstack @storages
    Scenario: Check attached storages
        Given I have running server M1
        Then I save volumes configuration in 'HostUp' message in M1
        And directory '/media/ebsmount' exist in M1
        And directory '/media/raidmount' exist in M1
        And I create 100 files in '/media/ebsmount' in M1
        And I create 100 files in '/media/raidmount' in M1

    @ec2 @cloudstack @rackspaceng @eucalyptus @reboot
    Scenario: Linux reboot
        Given I have running server M1
        When I reboot server M1
        And Scalr receives RebootFinish from M1

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @scripting
    Scenario: Execute script on Linux
        Given I have running server M1
        When I execute script 'Linux ping-pong' synchronous on M1
        And I see script result in M1
        And script output contains 'pong' in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @scripting
    Scenario: Execute non-ascii script on Linux
        Given I have running server M1
        When I execute script 'Non ascii script' synchronous on M1
        Then I see script result in M1
        And script output contains 'Non_ascii_script' in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack @scripting
    Scenario: Verify hidden global variable
        Given I have running server M1
        And file '/etc/profile.d/scalr_globals.sh' not contain 'revizor_hidden_var' in M1
        When I execute script 'Verify hidden variable' synchronous on M1
        Then I see script result in M1
        And script output contains 'REVIZOR_HIDDEN_VARIABLE' in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @restart
    Scenario: Restart scalarizr
        Given I have running server M1
        When I reboot scalarizr in M1
        And see 'Scalarizr terminated' in M1 log
        And not ERROR in M1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @event
    Scenario: Custom event
        Given I define event 'TestEvent'
        And I attach a script 'TestingEventScript' on this event
        When I execute 'szradm --fire-event TestEvent file1=/tmp/f1 file2=/tmp/f2' in M1
        Then Scalr sends TestEvent to M1
        And server M1 contain '/tmp/f1'
        And server M1 contain '/tmp/f2'

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @deploy
    Scenario: Check deploy action
        Given I have running server M1
        When I deploy app with name 'deploy-test'
        And Scalr sends Deploy to M1
        Then Scalr receives DeployResult from M1
        And deploy task deployed

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @restartfarm
    Scenario: Restart farm
        When I stop farm
        And wait all servers are terminated
        Then I start farm with delay
        And I expect server bootstrapping as M1
        And scalarizr version from system repo is last in M1

    @ec2 @openstack @storages
    Scenario: Check attached storages after restart farm
        Given I have running server M1
        Then volumes configuration in 'HostInitResponse' message in M1 is old
        And directory '/media/ebsmount' exist in M1
        And directory '/media/raidmount' exist in M1
        And count of files in directory '/media/ebsmount' is 100 in M1
        And count of files in directory '/media/raidmount' is 100 in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack @stopresume
    Scenario: Stop/resume on init policy
        When I suspend server M1
        Then I wait server M1 in suspended state
        And Scalr sends BeforeHostTerminate to M1
        And Scalr receives HostDown from M1
        Then I expect server bootstrapping as M2
        When I resume server M1
        Then I wait server M1 in running state
        And Scalr receives HostUp from M1

    @ec2 @gce @cloudstack @rackspaceng @openstack @stopresume
    Scenario: Stop/resume on reboot policy
        When I change suspend policy in role to reboot
        And I suspend server M1
        Then I wait server M1 in suspended state
        And Scalr receives HostDown from M1
        And I wait 5 minutes
        When I resume server M1
        Then I wait server M1 in running state
        And Scalr receives RebootFinish from M1