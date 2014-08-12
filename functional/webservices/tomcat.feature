Using step definitions from: steps/common_steps
Feature: Minimal test for bootstrapping tomcat role

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstraping tomcat role
        Given I have a an empty running farm
        When I add tomcat role to this farm
        Then I expect server bootstrapping as T1
        And 8080 port is listen on T1
        And 8443 port is listen on T1