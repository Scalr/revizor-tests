Feature: MongoDB shard 2x2 test

    Scenario: Bootstraping MongoDB role
        Given I have a an empty running farm
        When I add mongodb role to this farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
        And M1 hostname is mongo-0-0
        And port 27018 is listen in M1
        And port 27017 is listen in M1
        And port 27019 is listen in M1

    Scenario: Upscale to 1x2
        When I add replicaset
        And wait 2 servers is running
        And servers [0-0,0-1] in replicaset R1

    Scenario: Upscale to 2x2
        When I add shard
        Then I expect server bootstrapping as M2
        And scalarizr version is last in M2
        And M2 hostname is mongo-1-0
        And wait 4 servers is running
        And servers [1-0,1-1] in replicaset R2
        And shard status have 2 replicaset

	@restart_farm
    Scenario: Check start/stop farm
        When I start terminate cluster
        And wait cluster status terminated
        And I stop farm
        When I start farm
        And wait 4 servers is running
        And shard status have 2 replicaset
