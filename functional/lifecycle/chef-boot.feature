Using step definitions from: steps/common_steps, steps/chef_boot_steps, steps/lifecycle_steps
Feature: Check chef attributes set

    @ec2 @gce @cloudstack @openstack @rackspaceng
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
        And chef log in M1 contains 'revizor_chef_variable=REVIZOR_CHEF_VARIABLE_VALUE_WORK'

    @ec2 @gce @cloudstack @openstack @rackspaceng @openstack
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

    @ec2 @gce @cloudstack @rackspaceng @openstack @restartfarm
    Scenario: Cleanup farm
        When I stop farm
        And wait all servers are terminated

    @ec2 @gce @cloudstack @openstack @rackspaceng
    Scenario: Bootstrapping role with chef-solo
        Given I have a clean and stopped farm
        When I add role to this farm with chef-solo
        When I start farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
        And file '/root/chef_solo_result' exist in M1

    @ec2 @gce @cloudstack @openstack @rackspaceng
    Scenario: Bootstrapping role with chef-solo from public repo
        Given I have a clean and stopped farm
        When I add role to this farm with chef-solo-public
        When I start farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
        And nginx is running on M1
        Then I restart service www and pid has been changed on M1
        And nginx is running on M1

