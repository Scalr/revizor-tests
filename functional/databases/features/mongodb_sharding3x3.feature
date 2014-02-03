Feature: MongoDB shard 3x3 test

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstraping MongoDB role
        Given I have a an empty running farm
        When I add mongodb role to this farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
        And hostname in M1 is valid
        And port 27018 is listen in M1
        And port 27017 is listen in M1
        And port 27019 is listen in M1
        And mongodb log rotated on M1 and new created with 644 rights

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Upscale to 1x2
        When I add replicaset
        And wait 2 servers is running
        And servers [0-0,0-1] in replicaset R1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Upscale to 2x2
        When I add shard
        Then I expect server bootstrapping as M2
        And scalarizr version is last in M2
        And hostname in M2 is valid
        And wait 4 servers is running
        And servers [1-0,1-1] in replicaset R2
        And shard status have 2 replicaset

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Check start/stop farm
        When I start terminate cluster
        And wait cluster status terminated
        And I stop farm
        When I start farm
        And wait 4 servers is running
        And shard status have 2 replicaset

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Upscale to 2x3
        When I add replicaset
        And wait 6 servers is running
        And servers [0-0,0-1,0-2] in replicaset R1
        And servers [1-0,1-1,1-2] in replicaset R2

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Upscale to 3x3
        When I add shard
        Then I expect server bootstrapping as M3
        And scalarizr version is last in M3
        And wait 9 servers is running
        And servers [2-0,2-1,2-2] in replicaset R3

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Test termination
        Given I random terminate 5 servers
        And wait 9 servers is running
        And servers [0-0,0-1,0-2] in replicaset R1
        And servers [1-0,1-1,1-2] in replicaset R2
        And servers [2-0,2-1,2-2] in replicaset R3
        And shard status have 3 replicaset
        When I start terminate cluster
        And wait all servers are terminated
        And I stop farm