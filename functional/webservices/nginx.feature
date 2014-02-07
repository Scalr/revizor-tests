Using step definitions from: steps/common_steps, steps/apache_steps, steps/nginx_steps
Feature: Nginx load balancer role test with apache backends

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstraping nginx role
        Given I have a an empty running farm
        When I add www role to this farm
        Then I expect server bootstrapping as W1
        And scalarizr version is last in W1
        And nginx is running on W1
        And http get W1 contains 'No running app instances found'

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Adding custom role to upstream
        When I add base role to this farm
        Then I expect server bootstrapping as B1 in base role
        And I add base role as app role in W1 scalarizr config
        Then I restart service scalarizr in W1
        And I wait 1 minutes
        And W1 upstream list should contain B1
        And http get W1 contains 'Backend server did not respond in time'

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Clean up custom role
        When I delete base role from this farm
        And I remove base role from W1 scalarizr config
        Then I restart service scalarizr in W1
        And I wait 1 minutes
        And W1 upstream list should not contain B1
        And W1 upstream list should be default

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Adding app to upstream
        When I add app role to this farm
        And bootstrap 2 servers as (A1, A2) in app role
        Then W1 upstream list should contains A1, A2

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Removing app server
        When I terminate server A2 with decrease
        And I wait 1 minutes
        Then W1 upstream list should not contain A2
        But W1 upstream list should contain A1
        And Scalr sends HostDown to W1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: HTTP proxying
        When I create domain D1 to www role
        And I add virtual host H1 to app role and domain D1
        Then D1 resolves into W1 ip address
        And http get domain D1 matches H1 index page
        And my IP in A1 D1 access logs

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: HTTPS proxying
        When I create domain D2 to www role
        And I add ssl virtual host H2 to app role and domain D2
        Then D2 resolves into W1 ip address
        And http get domain D2 matches H2 index page
        And https get domain D2 matches H2 index page
        And domain D2 contains valid Cert and CACert
        And my IP in A1 D2 ssl access logs

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Rebundle nginx server
        When I create server snapshot for W1
        Then Bundle task created for W1
        And Bundle task becomes completed for W1

    @ec2 @gce @cloudstack @rackspaceng @openstack @rebundle
    Scenario: Use new nginx role
        Given I have a an empty running farm
        Then I add to farm role created by last bundle task
        And I expect server bootstrapping as W2
        And W2 upstream list should not contain A1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Adding app to upstream after rebundle
        When I add app role to this farm
        And I expect server bootstrapping as A3
        Then W2 upstream list should contain A3