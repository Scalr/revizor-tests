Feature: SzrAdm check backward compatibility

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstraping two servers with the app role
        Given I have a an empty running farm
        When I add app role to this farm with branch_latest
        Then I expect server bootstrapping as A1
        And scalarizr version is last in A1
        When I change branch to feature/szradm-rewrite for app role
        Then I increase minimum servers to 2 for app role
        Then I expect server bootstrapping as A2
        And scalarizr version is last in A2

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify szradm --queryenv get-latest-version
        When I run "szradm --queryenv get-latest-version" on A1
        And I run "szradm --queryenv get-latest-version" on A2
        Then I compare the obtained results of A1,A2
        And the key "version" has 1 record on A1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify szradm list-roles
        When I run "szradm list-roles" on A1
        And I run "szradm list-roles" on A2
        Then I compare the obtained results of A1,A2
        And table contains external-ip servers A1,A2

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify szradm list-roles -b base
        When I run "szradm list-roles -b base" on A1
        And I run "szradm list-roles -b base" on A2
        Then I compare the obtained results of A1,A2

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify szradm list-roles --behaviour base
        When I run "szradm list-roles --behaviour base" on A1
        And I run "szradm list-roles --behaviour base" on A2
        Then I compare the obtained results of A1,A2

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify szradm list-roles -b app
        When I run "szradm list-roles -b app" on A1
        And I run "szradm list-roles -b app" on A2
        Then I compare the obtained results of A1,A2
        And table contains external-ip servers A1,A2

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify szradm list-roles --behaviour app
        When I run "szradm list-roles --behaviour app" on A1
        And I run "szradm list-roles --behaviour app" on A2
        Then I compare the obtained results of A1,A2
        And table contains external-ip servers A1,A2

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify szradm --queryenv list-roles farm-role-id=$SCALR_FARM_ROLE_ID
        When I check an variable "SCALR_FARM_ROLE_ID" on A1
        And I check an variable "SCALR_FARM_ROLE_ID" on A2
        When I run "szradm --queryenv list-roles farm-role-id=$SCALR_FARM_ROLE_ID" on A1
        And I run "szradm --queryenv list-roles farm-role-id=$SCALR_FARM_ROLE_ID" on A2
        Then I compare the obtained results of A1,A2
        And the key "behaviour" has 1 record on A1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify szradm list-virtualhosts
        When I create domain D1 to app role
        And I add virtual host H1 to app role and domain D1
        Then Scalr sends VhostReconfigure to A1
        Then Scalr sends VhostReconfigure to A2
        And A1 has H1 in virtual hosts configuration
        And A2 has H1 in virtual hosts configuration
        Then I run "szradm list-virtualhosts" on A1
        And I run "szradm list-virtualhosts" on A2
        Then I compare the obtained results of A1,A2
        And the key "hostname" has 1 record on A1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify szradm get-https-certificate
        When I run "szradm get-https-certificate" on A1
        And I run "szradm get-https-certificate" on A2
        Then I compare the obtained results of A1,A2
        And the key "cert" has 0 record on A1



    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify szradm get-ebs-mountpoints


    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify szradm list-messages

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify szradm message-details


    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify szradm fire-event

