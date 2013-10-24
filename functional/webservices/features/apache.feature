Feature: Apache application server role

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstraping apache role
        Given I have a an empty running farm
        When I add app role to this farm
        Then I expect server bootstrapping as A1
        And scalarizr version is last in A1
        And apache is running on A1
        And http get A1 contains default welcome message

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Adding virtual host
        When I add virtual host H1 to A1
        Then Scalr sends VhostReconfigure to A1
        And H1 resolves into A1 ip address
        And A1 has H1 in virtual hosts configuration
        And http get H1 matches H1 index page

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Adding ssl virtual host
        When I add ssl virtual host H2 to A1
        Then Scalr sends VhostReconfigure to A1
        And H2 resolves into A1 ip address
        And https get H2 matches H2 index page
        And response contains valid Cert and CACert

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Removing virtual host
        Given I have virtual host H1 assigned to app role
        When I remove virtual host H1
        Then Scalr sends VhostReconfigure to A1
        And A1 has no H1 in virtual host configuration
        But A1 has H2 in virtual hosts configuration

    @ec2 @gce @cloudstack @rackspaceng @openstack @restartfarm
    Scenario: Restart farm
        When I stop farm
        And wait all servers are terminated
        Then I start farm
        And I expect server bootstrapping as A1
        And scalarizr version is last in A1
        Then H2 resolves into A1 new ip address
        And https get H2 matches H2 index page