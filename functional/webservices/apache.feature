Using step definitions from: steps/common_steps, steps/apache_steps
Feature: Apache application server role

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstraping apache role
        Given I have a an empty running farm
        When I add app role to this farm
        Then I expect server bootstrapping as A1
        And scalarizr version is last in A1
        And apache is running on A1
        And http get A1 contains default welcome message

    @ec2 @cloudstack @rackspaceng @openstack
    Scenario: Apache start after scalarizr restart
        Given apache is running on A1
        Then I stop service app and pid has been changed on A1
        And apache is not running on A1
        Then I restart service scalarizr and pid has been changed on A1
        And apache is running on A1
        And http get A1 contains default welcome message

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
        And I add ssl virtual host H2 with key revizor-key to app role and domain D2
        Then Scalr sends VhostReconfigure to A1
        And D2 resolves into A1 ip address
        And https get domain D2 matches H2 index page
        And domain D2 contains valid Cert and CACert

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Adding second ssl virtual host
        When I create domain D3 to app role
        And I add ssl virtual host H3 with key revizor2-key to app role and domain D3
        Then Scalr sends VhostReconfigure to A1
        And D3 resolves into A1 ip address
        And https get domain D3 matches H3 index page
        And domain D2,D3 contains valid Cert and CACert into A1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Removing virtual host
        When I remove from web interface virtual host H1
        Then Scalr sends VhostReconfigure to A1
        And A1 has not H1 in virtual host configuration
        But A1 has H2 in virtual hosts configuration

    @ec2 @cloudstack @rackspaceng
    Scenario: Virtual host auto update
        When I stop service scalarizr and pid has been changed on A1
        Then D2 resolves into A1 ip address
        And A1 has H2 in virtual hosts configuration
        Then I remove from web interface virtual host H2
        And I start service scalarizr and pid has been changed on A1
        And http get domain D2 matches H2 index page
        Then I reboot server A1
        And Scalr receives RebootFinish from A1
        And A1 has not H2 in virtual host configuration
        And http not get domain D2 matches H2 index page

    @ec2 @cloudstack @rackspaceng
    Scenario: Virtual host fail-safe mechanism
        Then I create domain D4 to app role
        And I add virtual host H4 to app role and domain D4
        Then Scalr sends VhostReconfigure to A1
        When D4 resolves into A1 ip address
        And A1 has H4 in virtual hosts configuration
        And http get domain D4 matches H4 index page
        Then I change the http virtual host H4 template invalid data
        Then Scalr sends VhostReconfigure to A1
        And I restart service app and pid has been changed on A1
        And apache is running on A1
        And http get domain D4 matches H4 index page
        When I remove from web interface virtual host H4
        Then Scalr sends VhostReconfigure to A1
        And A1 has not H4 in virtual host configuration

    @ec2 @gce @cloudstack @rackspaceng @openstack @restartfarm
    Scenario: Restart farm
        When I stop farm
        And wait all servers are terminated
        Then I start farm
        And I expect server bootstrapping as A1
        And scalarizr version is last in A1
        Then D3 resolves into A1 new ip address
        And https get domain D3 matches H3 index page

    @ec2 @gce @cloudstack @rackspaceng @openstack @restartfarm
    Scenario: Change the status of by api
        Given apache is running on A1
        Then I stop service app and pid has been changed on A1 by api
        And apache is not running on A1
        Then I start service app and pid has been changed on A1 by api
        And apache is running on A1
        Then I restart service app and pid has been changed on A1 by api
        And apache is running on A1
        Then I reload service app on A1 by api
        And https get domain D3 matches H3 index page
