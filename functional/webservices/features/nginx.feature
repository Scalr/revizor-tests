Feature: Nginx load balancer role test with apache backends

    Scenario: Bootstraping nginx role
        Given I have a an empty running farm
        When I add www role to this farm
        Then I expect server bootstrapping as W1
        And scalarizr version is last in W1
        And nginx is running on W1
        And http get W1 contains 'No running app instances found'

    Scenario: Adding app to upstream
        When I add app role to this farm
        And bootstrap 1+1 as (A1, A2)
        Then W1 upstream list should contains A1, A2

    Scenario: Removing app server
        When I terminate server A2 with decrease
        Then W1 upstream list should not contain A2
        But W1 upstream list should contain A1

    Scenario: HTTP proxying
        When I add virtual host H1 assigned to app role
        Then H1 resolves into W1 ip address
        And http get H1 matches H1 index page
        And my IP in A1 H1 access logs

    Scenario: HTTPS proxying
        When I add ssl virtual host H2 assigned to app role
        Then H2 resolves into W1 ip address
        Then https get H2 matches H2 index page
        And response contains valid Cert and CACert
        And my IP in A1 H2 ssl access logs

    @ec2 @gce @cloudstack @rackspaceng @rebundle
    Scenario: Rebundle nginx server
        When I create server snapshot for W1
        Then Bundle task created for W1
        And Bundle task becomes completed for W1

    @ec2 @gce @cloudstack @rackspaceng @rebundle
    Scenario: Use new nginx role
        Given I have a an empty running farm
        Then I add to farm role created by last bundle task
        And I expect server bootstrapping as W2
        And W2 upstream list should not contain A1

    Scenario: Adding app to upstream after rebundle
        When I add app role to this farm
        And I expect server bootstrapping as A3
        Then W2 upstream list should contain A3