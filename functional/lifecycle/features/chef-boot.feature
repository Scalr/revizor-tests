Feature: Check chef attributes set

    @ec2 @gce @cloudstack @rackspaceng
    Scenario: Bootstrapping chef role firstly
        Given I have a clean and stopped farm
        When I add role to this farm with chef
        When I start farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
        And process 'memcached' has options '-m 1024' in M1
        And process 'chef-client' has options '--daemonize' in M1
        And chef node_name in M1 set by global hostname

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify Scalr delete chef-fixtures
        When I stop farm
        And wait all servers are terminated
        Then I start farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
        And process 'memcached' has options '-m 1024' in M1
        And process 'chef-client' has options '--daemonize' in M1
        And chef node_name in M1 set by global hostname

    @ec2 @gce @cloudstack @rackspaceng @openstack @restartfarm
    Scenario: Stop farm softly
        When I stop farm
        And wait all servers are terminated