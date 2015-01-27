Using step definitions from: steps/common_steps, steps/lifecycle_steps, steps/chef_boot_steps
Feature: Linux server resume strategy
    In order to check resume strategy
    I monitoring server state changes

    @ec2 @gce @openstack @cloudstack @boot
    Scenario: Bootstraping
        Given I have a clean and stopped farm
        And I add role to this farm with chef,storages
        When I start farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1

    @ec2 @gce @openstack @cloudstack @storages
    Scenario: Check attached storages
        Given I have running server M1
        And disk types in role are valid
        And directory '/media/diskmount' exist in M1
        And directory '/media/raidmount' exist in M1
        And I create 100 files in '/media/diskmount' in M1
        And I create 100 files in '/media/raidmount' in M1

    @ec2 @gce @openstack @storages @fstab
    Scenario: Verify attached storages in fstab
        When I save mount table on M1
        And disk from M1 mount points for '/media/diskmount' exist in fstab on M1
        And disk from M1 mount points for '/media/raidmount' exist in fstab on M1

    @ec2 @gce @openstack @cloudstack @chef
    Scenario: Verify chef deployment
        When I save chef bootstrap stats on M1
        And process 'memcached' has options '-m 1024' in M1
        And process 'chef-client' has options '--daemonize' in M1
        And chef node_name in M1 set by global hostname

    @ec2 @gce @stopresume
    Scenario: Stop/resume on init policy
        When I suspend server M1
        Then Scalr sends BeforeHostTerminate to M1
        And I wait server M1 in suspended state
        Then I expect server bootstrapping as M2
        When I resume server M1
        Then I wait server M1 in running state
        And Scalr receives HostUp from M1

    @openstack @cloudstack @stopresume
    Scenario: Stop/resume on reboot policy
        When I suspend server M1
        And I wait server M1 in suspended state
        Then I expect server bootstrapping as M3
        When I resume server M1
        Then I wait server M1 in running state
        And Scalr receives RebootFinish from M1

    @ec2 @gce @chef
    Scenario: Verify chef deployment after resume on init policy
        When I check chef bootstrap stats on M1
        And process 'memcached' has options '-m 1024' in M1
        And process 'chef-client' has options '--daemonize' in M1
        And chef node_name in M1 set by global hostname

    @openstack @cloudstack @chef
    Scenario: Verify chef after resume on reboot policy
        When I check chef bootstrap stats on M1
        And process memcached is not running in M1
        And process 'chef-client' has options '--daemonize' in M1
        And chef node_name in M1 set by global hostname

  @ec2 @gce @openstack @cloudstack @storages
    Scenario: Check attached storages after resume
        And directory '/media/diskmount' exist in M1
        And directory '/media/raidmount' exist in M1
        And count of files in directory '/media/raidmount' is 100 in M1

    @ec2 @gce @openstack @storages @fstab
    Scenario: Verify attached storages in fstab after resume
        And disk from M1 mount points for '/media/diskmount' exist in fstab on M1
        And disk from M1 mount points for '/media/raidmount' exist in fstab on M1
