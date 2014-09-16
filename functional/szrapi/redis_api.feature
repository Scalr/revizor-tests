Using step definitions from: steps/common_api_steps, steps/redis_api_steps
Feature: Redis database server role, api tests

    @ec2 @gce @cloudstack @rackspaceng @openstack @bootstrap
    Scenario: Bootstraping Redis role with multi instance
        Given I have a an empty running farm
        When I add redis role to this farm with 2 redis processes
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
        Then I run "RedisApi" command "list_processes" on M1
        And number of redis instance is 2
        And redis instance ports is 6379,6380
        Then I run "RedisApi" command "get_service_status" on M1
        And all redis instance is running
        And not ERROR in M1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Launch additional redis instances
        Given I run "RedisApi" command "launch_processes" on M1 with arguments:
            | num | ports              | passwords                | async |
            | 3   | [6381, 6382, 6383] | MULTI-INSTANCE-PASSWORDS | False |
        Then I run "RedisApi" command "list_processes" on M1
        And number of redis instance is 5 on M1
        And redis instance ports is 6379,6380,6381,6382,6383
        Then I run "RedisApi" command "get_service_status" on M1
        And all redis instance is running
        And not ERROR in M1 scalarizr log