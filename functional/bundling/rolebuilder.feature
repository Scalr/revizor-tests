Using step definitions from: steps/rolebuilder_steps
Feature: Build all behaviors via rolebuilder and check server running

    @ec2 @gce @rackspaceng
    Scenario Outline: Build role and test it
        Given I have a an empty running farm
        When I start build role with behaviors <behaviors>
        And Build task started
        Then Build task completed
        And I have new role id
        When I add to farm role created by last bundle task
        Then I expect server bootstrapping as M1

    Examples:
      | behaviors  |
      | mysql2,app |
      | percona,www |
      | redis,mongodb,haproxy |
      | postgresql,memcached,rabbitmq |