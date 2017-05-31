Using step definitions from: steps/common_steps, steps/lifecycle_steps, steps/scripting_steps, steps/szradm_steps
Feature: Linux server lifecycle
    In order to manage server lifecycle
    As a scalr user
    I want to be able to monitor server state changes

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @azure @boot
    Scenario: Bootstraping
        Given I have a clean and stopped farm
        And I add role to this farm with storages,noiptables
        When I start farm
        Then I see pending server M1
        And I wait and see running server M1
        And instance vcpus info not empty for M1
        And scalarizr version is last in M1
        And hostname in M1 is valid
        And ports [8008,8010,8012,8013,8014] not in iptables in M1

    @ec2 @cloudstack @gce @storages
    Scenario: Check attached storages
        Given I have running server M1
        Then I save volumes configuration in 'HostUp' message in M1
        And disk types in role are valid
        And directory '/media/diskmount' exist in M1
        And directory '/media/raidmount' exist in M1
        And directory '/media/partition' exist in M1
        And I create 100 files in '/media/diskmount' in M1
        And I create 100 files in '/media/raidmount' in M1

    @ec2 @partition
    Scenario: Create volume snapshot
        When I reconfigure device partitions for '/media/partition' on M1
        And I trigger snapshot creation from volume for '/media/partition' on role
        Then Volume snapshot creation become completed

    @ec2 @cloudstack @gce @storages @fstab
    Scenario: Verify attached storages in fstab
        When I save mount table on M1
        And disk from M1 mount points for '/media/diskmount' exist in fstab on M1
        And disk from M1 mount points for '/media/raidmount' exist in fstab on M1

    @ec2 @cloudstack @gce @rackspaceng @eucalyptus @azure @reboot
    Scenario: Linux reboot
        Given I have running server M1
        When I reboot server M1
        And Scalr receives RebootFinish from M1

    @ec2 @cloudstack @storages @fstab
    Scenario: Verify attached storages in fstab after reboot
        And disk from M1 mount points for '/media/diskmount' exist in fstab on M1
        And disk from M1 mount points for '/media/raidmount' exist in fstab on M1

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @azure @scripting
    Scenario: Execute script on Linux
        Given I have running server M1
        When I execute script 'Linux ping-pong' synchronous on M1
        And I see script result in M1
        And script output contains 'pong' in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @azure @scripting
    Scenario: Execute non-ascii script on Linux
        Given I have running server M1
        When I execute script 'Non ascii script' synchronous on M1
        Then I see script result in M1
        And script output contains 'Non_ascii_script' in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @azure @scripting
    Scenario: Check non-ascii script output on Linux
        Given I have running server M1
        When I execute script 'non-ascii-output' synchronous on M1
        Then I see script result in M1
        And script output contains 'Ã¼' in M1
        And script output contains 'クマ' in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack @azure @scripting
    Scenario: Verify hidden global variable
        Given I have running server M1
        And file '/etc/profile.d/scalr_globals.sh' not contain 'revizor_hidden_var' in M1
        When I execute script 'Verify hidden variable' synchronous on M1
        Then I see script result in M1
        And script output contains 'REVIZOR_HIDDEN_VARIABLE' in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @azure @restart
    Scenario: Restart scalarizr
        Given I have running server M1
        When I reboot scalarizr in M1
        And see "Scalarizr terminated" in M1 log
        And not ERROR in M1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @azure @event
    Scenario: Custom event
        Given I define event 'TestEvent'
        And I attach a script 'TestingEventScript' on this event
        When I execute 'szradm --fire-event TestEvent file1=/tmp/f1 file2=/tmp/f2' in M1
        Then Scalr sends TestEvent to M1
        And server M1 contain '/tmp/f1'
        And server M1 contain '/tmp/f2'

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @azure @event
    Scenario: Caching custom event parameters
        Given I define event 'TestEvent'
        And I attach a script 'TestingEventScript' on this event
        When I execute 'szradm --fire-event TestEvent file1=/tmp/nocache1 file2=/tmp/nocache2' in M1
        Then Scalr sends TestEvent to M1
        And server M1 contain '/tmp/nocache1'
        And server M1 contain '/tmp/nocache2'

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @azure @szradm
    Scenario: Verify szradm list-roles
        When I run "szradm -q list-roles" on M1
        And output contain M1 external ip
        When I run "szradm --queryenv get-latest-version" on M1
        And the key "version" has 1 record on M1
        When I run "szradm list-messages" on M1
        And the key "name" has record "HostUp" on M1

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @azure @restartfarm
    Scenario: Stop farm
        When I stop farm
        And wait all servers are terminated

    @ec2 @cloudstack @gce @storages
    Scenario: Delete attached storage
        When I save device for '/media/diskmount' for role
        And I delete saved device '/media/diskmount'

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @azure @restartfarm
    Scenario: Start farm
        When I start farm with delay
        Then I expect server bootstrapping as M1
        And scalarizr version from system repo is last in M1

    @ec2 @cloudstack @gce @storages
    Scenario: Check attached storages after restart farm
        Given I have running server M1
        Then volumes configuration in 'HostInitResponse' message in M1 is old
        And directory '/media/diskmount' exist in M1
        And directory '/media/raidmount' exist in M1
        And count of files in directory '/media/raidmount' is 100 in M1
        And saved device for '/media/diskmount' for role is another

    @ec2 @gce @cloudstack @rackspaceng @openstack @azure @eucalyptus
    Scenario: Reboot on bootstraping
        Given I have a clean and stopped farm
        And I add role to this farm with init_reboot,small_linux_orchestration
        When I start farm
        And I see pending server M1
        When I wait server M1 in running state
        Then script Revizor last reboot executed in HostInit by user root with exitcode 0 for M1
        And script Revizor last reboot executed in HostUp by user root with exitcode 0 for M1
        And start time in Revizor last reboot scripts are different for M1
        And hostname in M1 is valid

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @failedbootstrap
    Scenario: Failed bootstrap by hostname
        Given I have a clean and stopped farm
        And I add role to this farm with failed_hostname
        When I start farm
        And I see pending server M1
        And I wait server M1 in failed state

    @ec2 @partition
    Scenario: Check partition table recognized as a non-blank volume
        Given I have a clean and stopped farm
        And I add role to this farm
        And I add new storage from volume snapshot to role
        When I start farm
        And I see pending server M1
        And I wait server M1 in failed state
