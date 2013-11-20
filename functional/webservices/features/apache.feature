Feature: Apache application server role

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstraping apache role
        Given I have a an empty running farm
        When I add app role to this farm
        Then I expect server bootstrapping as A1
        And scalarizr version is last in A1
        And apache is running on A1
        And http get A1 contains default welcome message
        And https get A1 contains default welcome message

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Adding virtual host
        When I create domain D1 to app role
        And I add virtual host H1 to app role and domain D1
        Then Scalr sends VhostReconfigure to A1
        And D1 resolves into A1 ip address
        And A1 has H1 in virtual hosts configuration
        And http get domain D1 matches H1 index page

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Adding ssl virtual host
        When I create domain D2 to app role
        And I add ssl virtual host H2 to app role and domain D2
        Then Scalr sends VhostReconfigure to A1
        And D2 resolves into A1 ip address
        And https get domain D2 matches H2 index page
        And domain D2 contains valid Cert and CACert

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Removing virtual host
        When I remove virtual host H1
        Then Scalr sends VhostReconfigure to A1
        And A1 has not H1 in virtual host configuration
        But A1 has H2 in virtual hosts configuration

    @ec2 @cloudstack @rackspaceng
    Scenario: Virtual host auto update
        Then I create domain D3 to app role
        And I add virtual host H3 to app role and domain D3
        Then I stop scalarizr on A1
        And D3 resolves into A1 ip address
        And A1 has H3 in virtual hosts configuration
        Then I remove virtual host H3
        And I start scalarizr on A1
        And http get domain D3 matches H3 index page
        Then I reboot server A1
        And Scalr receives RebootFinish from A1
        And A1 has not H3 in virtual host configuration
        And http get domain D3 matches H3 index page


    @ec2 @gce @cloudstack @rackspaceng @openstack @restartfarm
    Scenario: Restart farm
        When I stop farm
        And wait all servers are terminated
        Then I start farm
        And I expect server bootstrapping as A1
        And scalarizr version is last in A1
        Then D2 resolves into A1 new ip address
        And https get domain D2 matches H2 index page