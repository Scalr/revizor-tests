Feature: Memcached service standart port 11211 with behavior memcached

    @boot
    Scenario: Bootstraping Memcached role
        Given I have a an empty running farm
        When I add memcached role to this farm
        Then I expect server bootstrapping as M1
        And memcached is running on M1
        And scalarizr version is last in M1

    @init_client @set_item
    Scenario: Set new items are at the top of the LRU.
        I initialize instance memcache Client on M1
        I run a "memcached_comand" to "set key" for new item on M1
        I run a "memcached_comand" to "get key" from item on M1

