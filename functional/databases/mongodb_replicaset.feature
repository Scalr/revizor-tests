Using step definitions from: steps/common_steps, steps/mongo_steps
Feature: MongoDB replica set

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstraping MongoDB role
        Given I have a an empty running farm
        When I add mongodb role to this farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
        And M1 hostname is mongo-0-0
        And port 27018 is listen in M1
        And port 27017 is listen in M1
        And port 27019 is listen in M1
        And mongodb log rotated on M1 and new created with 644 rights

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Upscale replica-set
        When I add replicaset
        Then I expect server bootstrapping as M2
        And scalarizr version is last in M2
        And M2 hostname is mongo-0-1
        And port 27018 is listen in M2
        And port 27017 is listen in M2
        And port 27019 is not listen in M2
        And port 27020 is listen in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Downscale replica-set
        When I delete replicaset
        And M1 is master
        Then I add small-sized database D1 on M1
        And I add replicaset
        Then I expect server bootstrapping as M3
        And scalarizr version is last in M3
        And wait M3 as replica have data in database D1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Upscale replica-set to 3 instance
        When I add replicaset
        Then I expect server bootstrapping as M4
        And scalarizr version is last in M4
        And port 27017 is not listen in M4
        And port 27018 is listen in M4
        And port 27019 is not listen in M4
        And port 27020 is not listen in all
        And replicaset status is valid on M4
        When I delete replicaset
        And M1 is master
        And port 27020 is listen only in M1