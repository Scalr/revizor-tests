Using step definitions from: steps/memcached_steps
Feature: Memcached service standart port 11211 with behavior memcached

    @ec2 @gce @cloudstack @rackspaceng @boot
    Scenario: Bootstraping Memcached role
        Given I have a an empty running farm
        When I add memcached role to this farm
        Then I expect server bootstrapping as M1
        And memcached is running on M1
        And scalarizr version is last in M1

    @ec2 @gce @cloudstack @rackspaceng @rebundle
     Scenario: Rebundle server
        When I create server snapshot for M1
        Then Bundle task created for M1
        And Bundle task becomes completed for M1

    @ec2 @gce @cloudstack @rackspaceng @rebundle
    Scenario: Use new role
        Given I have a an empty running farm
        When I add to farm role created by last bundle task
        Then I expect server bootstrapping as M2
        And memcached is running on M2

    @ec2 @gce @cloudstack @rackspaceng @memcached_client_verify
    Scenario: Set new items are at the top of the LRU.
        I initialize instance memcache Client on M2
        I run a "memcached_command" to "set key" for new item on M2
        I run a "memcached_command" to "get key" from item on M2

