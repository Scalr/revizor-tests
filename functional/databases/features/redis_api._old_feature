Feature: Redis database server with multi instance and use redis API

	@bootstrap
    Scenario: Bootstraping Redis role
        Given I have a an empty running farm
        When I add redis role to this farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
        And redis is running on M1

	@bootstrap
    Scenario: Setup replication
        When I increase minimum servers to 2 for redis role
        Then I expect server bootstrapping as M2
        And scalarizr version is last in M2
        And M2 is slave of M1

    Scenario: Add multi instance to master
        When I add 2 redis master instance to M1
        And count of redis instance is 3 in M1
        And 3 redis instances work in M1
        And 3 redis instances is master in M1
        And redis not started in M1 port 6379

    Scenario: Add multi instance to slave
        When I add 2 redis slave instance to M2
        And count of redis instance is 3 in M2
        And 3 redis instances work in M2
        And 3 redis instances is slave in M2

    Scenario: Check replication
        When I write data to redis 1 in M1
        Then I read data from redis 1 in M2
        When I write data to redis 2 in M1
        Then I read data from redis 2 in M2
        When I write data to redis 3 in M1
        Then I read data from redis 3 in M2

    Scenario: Delete one instance pair
        When I delete 1 redis instance in M1
        And count of redis instance is 2 in M1
        When I delete 1 redis instance in M2
        And count of redis instance is 2 in M2

