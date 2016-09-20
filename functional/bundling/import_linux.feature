Using step definitions from: steps/import_steps
Feature: Import server to scalr and use this role

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Executing import command on server running without userdata
        Given I have a server running in cloud
        Then I initiate the installation behaviors on the server
        And I install scalarizr to the server
        Then I trigger the Start building and run scalarizr
        And connection with scalarizr was established
        Then I trigger the Create role
        And Role has successfully been created

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Using new role
        Given I have a an empty running farm
        When I add to farm imported role
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Executing import command on server running with userdata
        Given I have a server with userdata running in cloud
#        Then I initiate the installation behaviors on the server
        And I install scalarizr to the server
        Then I trigger the Start building and run scalarizr
        And connection with scalarizr was established
        Then I trigger the Create role
        And Role has successfully been created

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Using new role 2
        Given I have a an empty running farm
        When I add to farm imported role
        Then I expect server bootstrapping as M2
        And scalarizr version is last in M2

