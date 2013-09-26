Feature: Nginx load balancer role test with apache backends

    @ec2 @gce @cloudstack @rackspaceng
    Scenario: Bootstraping nginx role
        Given I have a an empty running farm
        When I add www role to this farm
        Then I expect server bootstrapping as W1
        And scalarizr version is last in W1
        And nginx is running on W1
        And http get W1 contains 'No running app instances found'

    @ec2 @gce @cloudstack @rackspaceng
    Scenario: Adding custom role to upstream
        When I add base role to this farm
        Then I expect server bootstrapping as B1
        And I add base role as app role in W1 scalarizr config
        Then I restart service scalarizr in W1
        And I wait 1 minutes
        And W1 upstream list should contain B1
        And http get W1 contains 'Backend server did not respond in time'

    @ec2 @gce @cloudstack @rackspaceng
    Scenario: Clean up custom role
        When I delete base role from this farm
        And I remove base role from W1 scalarizr config
        Then I restart service scalarizr in W1
        And I wait 1 minutes
        And W1 upstream list should not contain B1
        And W1 upstream list should be default

    @ec2 @gce @cloudstack @rackspaceng
    Scenario: Adding app to upstream
        When I add app role to this farm
        And bootstrap 2 servers as (A1, A2)
        Then W1 upstream list should contains A1, A2

    @ec2 @gce @cloudstack @rackspaceng
    Scenario: Removing app server
        When I terminate server A2 with decrease
        And I wait 1 minutes
        Then W1 upstream list should not contain A2
        But W1 upstream list should contain A1
        And Scalr sends HostDown to W1

    @ec2 @gce @cloudstack @rackspaceng
    Scenario: HTTP proxying
        When I add virtual host H1 assigned to app role
        Then H1 resolves into W1 ip address
        And http get H1 matches H1 index page
        And my IP in A1 H1 access logs

    @ec2 @gce @cloudstack @rackspaceng
    Scenario: HTTPS proxying
        When I add ssl virtual host H2 assigned to app role
        Then H2 resolves into W1 ip address
        Then https get H2 matches H2 index page
        And response contains valid Cert and CACert
        And http get H2 matches H2 index page
        And my IP in A1 H2 ssl access logs

    @ec2 @gce @cloudstack @rackspaceng
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

    @ec2 @gce @cloudstack @rackspaceng
    Scenario: Adding app to upstream after rebundle
        When I add app role to this farm
        And I expect server bootstrapping as A3
        Then W2 upstream list should contain A3