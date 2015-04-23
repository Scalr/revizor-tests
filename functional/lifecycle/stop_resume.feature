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

    @ec2 @gce @openstack @cloudstack @storages @chef
    Scenario: Check attached storages and chef deployment
        Given I have running server M1
        And process 'memcached' has options '-m 1024' in M1
        And process 'chef-client' has options '--daemonize' in M1
        And chef node_name in M1 set by global hostname
        And I save chef bootstarp stat on M1
        And disk types in role are valid
        And directory '/media/diskmount' exist in M1
        And directory '/media/raidmount' exist in M1
        Then I create 100 files in '/media/diskmount' in M1
        And I create 100 files in '/media/raidmount' in M1
        When I save mount table on M1
        And disk from M1 mount points for '/media/diskmount' exist in fstab on M1
        And disk from M1 mount points for '/media/raidmount' exist in fstab on M1

    @ec2 @gce @stopresume
    Scenario: Stop/resume on init policy
        When I suspend server M1
        Then Scalr sends BeforeHostTerminate to M1
        And I wait server M1 in suspended state
        Then I expect server bootstrapping as M2
        When I resume server M1
        Then I wait server M1 in running state
        And Scalr receives HostUp from M1
        And process 'memcached' has options '-m 1024' in M1
        And process 'chef-client' has options '--daemonize' in M1
        And I check chef bootstarp stat on M1
        And directory '/media/diskmount' exist in M1
        And directory '/media/raidmount' exist in M1
        And disk from M1 mount points for '/media/diskmount' exist in fstab on M1
        And disk from M1 mount points for '/media/raidmount' exist in fstab on M1
        And count of files in directory '/media/raidmount' is 100 in M1
        And saved device for '/media/diskmount' for role is another


    @openstack @cloudstack @stopresume
    Scenario: Stop/resume on reboot policy
        Then I suspend server M1
        And I wait server M1 in suspended state
        Then I expect server bootstrapping as M3
        When I resume server M1
        Then I wait server M1 in running state
        And Scalr receives RebootFinish from M1
        And process 'memcached' has options '-m 1024' in M1
        And process 'chef-client' has options '--daemonize' in M1
        And I check chef bootstarp stat on M1
        And directory '/media/diskmount' exist in M1
        And directory '/media/raidmount' exist in M1
        And disk from M1 mount points for '/media/diskmount' exist in fstab on M1
        And disk from M1 mount points for '/media/raidmount' exist in fstab on M1
        And count of files in directory '/media/raidmount' is 100 in M1
        And saved device for '/media/diskmount' for role is another
