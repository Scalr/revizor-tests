Feature: MongoDB switch master ebs test

    Scenario: Bootstraping MongoDB role
        Given I have a an empty running farm
        When I add mongodb role to this farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
        And M1 hostname is mongo-0-0
        And port 27018 is listen in M1
        And port 27017 is listen in M1
        And port 27019 is listen in M1

    Scenario: Upscale replica-set
        When I add replicaset
        Then I expect server bootstrapping as M2
        And scalarizr version is last in M2
        And M2 hostname is mongo-0-1
        And port 27018 is listen in M2
        And port 27017 is listen in M2
        And port 27019 is not listen in M2
        And port 27020 is listen in M1
        And M1 is master
        
    Scenario: Restart master
        When I force terminate M1
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
        Then I create file in master
        And start terminate cluster
        And wait all servers are terminated
        And I stop farm
    
    Scenario: Check EBS
        When I start farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
        And I expect server bootstrapping as M2
        And scalarizr version is last in M2
        And master have file