Using step definitions from: steps/common_steps, steps/lifecycle_steps, steps/chef_boot_steps
Feature: Linux server resume strategy
    In order to check resume strategy
    I monitoring server state changes

    @ec2 @gce @cloudstack @boot
    Scenario: Bootstraping
        Given I have a clean and stopped farm
        And I add role to this farm with chef,storages,termination_preferences
        When I start farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1

    @ec2 @gce @cloudstack @storages
    Scenario: Check attached storages
        Given I have running server M1
        And disk types in role are valid
        And directory '/media/diskmount' exist in M1
        And directory '/media/raidmount' exist in M1
        And I create 100 files in '/media/diskmount' in M1
        And I create 100 files in '/media/raidmount' in M1

    @ec2 @gce @storages @fstab
    Scenario: Verify attached storages in fstab
        When I save mount table on M1
        And disk from M1 mount points for '/media/diskmount' exist in fstab on M1
        And disk from M1 mount points for '/media/raidmount' exist in fstab on M1

    @ec2 @gce @cloudstack @chef
    Scenario: Verify chef deployment
        When I save chef bootstrap stats on M1
        And process 'memcached' has options '-m 1024' in M1
        And process 'chef-client' has options '--daemonize' in M1
        And chef node_name in M1 set by global hostname

    @ec2 @gce @cloudstack @stopresume
    Scenario: Stop/resume
        When I suspend server M1
        Then BeforeHostTerminate (Suspend) event was fired by M1
        And Scalr sends BeforeHostTerminate to M1
        Then I wait server M1 in suspended state
        And HostDown (Suspend) event was fired by M1
        And server M1 exists on chef nodes list
        Then I expect new server bootstrapping as M2
        When I resume server M1
        Then I wait server M1 in resuming state
        Then Scalr receives RebootFinish from M1
        And ResumeComplete event was fired by M1
        Then I wait server M1 in running state
        And HostInit,BeforeHostUp events were not fired after M1 resume

    @ec2 @gce @cloudstack @chef
    Scenario: Verify chef after resume
        When I check chef bootstrap stats on M1
        And process memcached is not running in M1
        And process 'chef-client' has options '--daemonize' in M1
        And chef node_name in M1 set by global hostname

    @ec2 @gce @cloudstack @storages
    Scenario: Check attached storages after resume
        And directory '/media/diskmount' exist in M1
        And directory '/media/raidmount' exist in M1
        And count of files in directory '/media/raidmount' is 100 in M1

    @ec2 @gce @cloudstack @storages @fstab
    Scenario: Verify attached storages in fstab after resume
        And disk from M1 mount points for '/media/diskmount' exist in fstab on M1
        And disk from M1 mount points for '/media/raidmount' exist in fstab on M1

    @ec2 @gce @cloudstack
    Scenario: Verify Scalr delete chef nodes
        When I stop farm
        And wait all servers are terminated
        And server M1 not exists on chef nodes list

    @ec2 @gce @cloudstack @rackspaceng @openstack @stopresume @farmsuspend
    Scenario: Suspend/resume farm with nginx + apache roles configured with virtual host proxying in Apache
        Given I have a clean and stopped farm
        When I add www role to this farm
        When I add app role to this farm
        When I start farm
        Then I expect server bootstrapping as W1 in www role
        Then I expect server bootstrapping as A2 in app role
        And nginx is running on W1
        When I create domain D1 to www role
        And I add virtual host H1 to app role and domain D1
        And I add http proxy P1 to www role with H1 host to app role with ip_hash with private network
        When I suspend farm
        Then I wait farm in Suspended state
        And wait all servers are suspended
        When I resume farm
        Then I wait server W1 in resuming state
        Then I wait server A2 in resuming state
        Then Scalr receives RebootFinish from W1
        Then Scalr receives RebootFinish from A2
        And ResumeComplete event was fired by W1
        And ResumeComplete event was fired by A2
        Then I wait server W1 in running state
        Then I wait server A2 in running state
        And HostInit,BeforeHostUp events were not fired after W1 resume
        And HostInit,BeforeHostUp events were not fired after A2 resume
        And http get domain D1 matches H1 index page
