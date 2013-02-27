Feature: RabbitMQ test

    Scenario: Bootstraping RabbitMQ role
        Given I have a an empty running farm
        When I add rabbitmq role to this farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
        And M1 is hdd node
    
    Scenario: Upscale RabbitMQ role
        When I increase minimum servers to 3 for rabbitmq role
        Then I expect server bootstrapping as M2
        And scalarizr version is last in M1
        And I expect server bootstrapping as M3
        And scalarizr version is last in M1
        Then I check 3 nodes in cluster on M1
        And 2 nodes are hdd and 1 node is ram on M1
    
    Scenario: Check persistent queue
        When I add user to M1
        And I add queue to M1
        And I add message to M1
        And I add vhost to M1
        Then I enable control panel
        And control panel work

    @restart_farm
    Scenario: Restart farm
        When I terminate farm
        And wait all servers are terminated
        Then I start farm
        And I expect server bootstrapping as M4
        And scalarizr version is last in M4
        And I expect server bootstrapping as M5
        And I expect server bootstrapping as M6
        And user exists in M4
        And queue exists in M4
        And message exists in M4
        Then I enable control panel
        And control panel work