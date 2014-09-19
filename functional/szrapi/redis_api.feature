Using step definitions from: steps/common_api_steps, steps/redis_api_steps
Feature: Redis database server role, api tests

    @ec2 @gce @cloudstack @rackspaceng @openstack @bootstrap
    Scenario: Bootstraping Redis role with multiple instances
        Given I have a an empty running farm
        When I add redis role to this farm with 2 redis processes
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
        Then I run "RedisApi" command "list_processes" on M1
        And number of redis instance is 2
        And redis instance ports is 6379,6380
        Then I run "RedisApi" command "get_service_status" on M1
        And 6379,6380 redis instance is running
        And not ERROR in M1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack @bootstrap
    Scenario: Reset instances passwords
        Given I run "RedisApi" command "list_processes" on M1
        Then I run "RedisApi" command "reset_password" on M1 with arguments:
            | port | new_passwords     |
            | 6379 | INSTANCE-PASSWORD |
        And password for instance 6379 was changed on M1
        Then I run "RedisApi" command "reset_password" on M1 with arguments:
            | port |
            | 6380 |
        And password for instance 6380 was changed on M1
        And not ERROR in M1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Launch additional redis instances
        When I run "RedisApi" command "launch_processes" on M1 with arguments:
            | num | ports              | passwords                | async |
            | 3   | [6381, 6382, 6383] | MULTI-INSTANCE-PASSWORDS | False |
        Then I run "RedisApi" command "list_processes" on M1
        And number of redis instance is 5 on M1
        And redis instance ports is 6379,6380,6381,6382,6383
        Then I run "RedisApi" command "get_service_status" on M1
        And all redis instance is running
        And not ERROR in M1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack @aof
    Scenario: Change redis-server instances status (stop, shutdown)
        Given I write test data to 6379 redis instance on M1
        When I run "RedisApi" command "stop_service" and pid has been changed on M1 with arguments:
            | ports |
            | 6379  |
        Then I run "RedisApi" command "shutdown_processes" and pid has been changed on M1 with arguments:
            | ports  | remove_data | async |
            | [6380] | False       | False |
        And redis instance with port 6380 has not configuration on M1
        And data from 6379 was not removed on M1
        Then I run "RedisApi" command "list_processes" on M1
        And number of redis instance is 3 on M1
        And redis instance ports is 6381,6382,6383
        Then I run "RedisApi" command "get_service_status" on M1
        And 6379.6380 redis instance is not running
        And not ERROR in M1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack @aof
    Scenario: Change redis-server instances status (start, restart)
        Given When I run "RedisApi" command "start_service" and pid has been changed on M1 with arguments:
            | ports  |
            | [6379] |
        And number of redis instance is 4 on M1
        And redis instance ports is 6379,6381,6382,6383
        Then I run "RedisApi" command "get_service_status" on M1
        And all redis instance is running
        Then I run "RedisApi" command "restart_service" and pid has been changed on M1 with arguments:
            | ports |
            | 6380  |
        Then I read test data from 6379 redis instance on M1
        And not ERROR in M1 scalarizr log


