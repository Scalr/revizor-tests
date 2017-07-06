Using step definitions from: steps/common_steps, steps/chef_boot_steps, steps/lifecycle_steps, steps/scripting_steps
Feature: Check chef attributes set

    @ec2 @vmware @gce @cloudstack @openstack @rackspaceng @azure @systemd
    Scenario: Bootstrapping chef role firstly
        Given I have a clean and stopped farm
        When I add role to this farm with chef
        When I start farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
        And process 'memcached' has options '-m 1024' in M1
        And process 'chef-client' has options '--daemonize' in M1
        And server M1 exists on chef nodes list
        And chef node_name in M1 set by global hostname
        And chef log in M1 contains "revizor_chef_variable=REVIZOR_CHEF_VARIABLE_VALUE_WORK"

    @ec2 @vmware @gce @cloudstack @openstack @rackspaceng @azure @systemd
    Scenario: Checking changes INTERVAL config
        When I change chef-client INTERVAL to 15 sec on M1
        And restart chef-client process on M1
        Then I verify that this INTERVAL 15 appears in the startup line on M1
        And I wait and see that chef-client runs more than INTERVAL 15 on M1

    @ec2 @vmware @gce @cloudstack @openstack @rackspaceng @azure @openstack
    Scenario: Verify Scalr delete chef-fixtures
        When I stop farm
        And wait all servers are terminated
        And server M1 not exists on chef nodes list
        Then I start farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
        And process 'memcached' has options '-m 1024' in M1
        And process 'chef-client' has options '--daemonize' in M1
        And chef node_name in M1 set by global hostname

    @ec2 @vmware @gce @cloudstack @rackspaceng @openstack @azure @restartfarm
    Scenario: Cleanup farm
        When I stop farm
        And wait all servers are terminated

    @ec2 @vmware @gce @cloudstack @openstack @azure @rackspaceng
    Scenario Outline: Bootstrapping role with chef-solo
        Given I have a clean and stopped farm
        When I add role to this farm with <settings>
        When I start farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
        And file '/root/<settings>' exist in M1

    Examples:
      | settings                |
      | chef-solo-private       |
      | chef-solo-public        |
      | chef-solo-public-branch |

    @ec2 @vmware @gce @cloudstack @openstack @azure @rackspaceng
    Scenario: Chef bootstrap failure
        Given I have a clean and stopped farm
        When I add role to this farm with chef-fail
        When I start farm
        Then I see failed server M1
        And Initialization was failed on "BeforeHostUp" phase with "/usr/bin/chef-client exited with code 1" message on M1
        And chef log in M1 contains "ERROR: undefined method `fatal!'"
        And chef bootstrap failed in M1

    @ec2 @vmware @gce @cloudstack @openstack @azure @rackspaceng
    Scenario: Bootstrapping from chef role
        Given I have a clean and stopped farm
        When I add role to this farm with chef-role
        When I start farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
        And server M1 exists on chef nodes list
        And chef node_name in M1 set by global hostname
        And chef log in M1 contains "revizor_chef_variable=REVIZOR_CHEF_VARIABLE_VALUE_WORK"
