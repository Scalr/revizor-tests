Feature: SzrAdm check backward compatibility

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstraping two servers with the app role
        Given I have a an empty running farm
        When I add app role to this farm with branch_latest
        Then I expect server bootstrapping as A1
        And scalarizr version is last in A1
        When I change branch to feature/szradm-rewrite for app role
        When I increase minimum servers to 2 for app role
        Then I expect server bootstrapping as A2
        And scalarizr version is last in A2

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify szradm --queryenv get-latest-version
        When I run "szradm --queryenv get-latest-version" on A1
        And I run "szradm --queryenv get-latest-version" on A2
        Then I compare the obtained results of A1,A2
        And The key "version" has a non-empty result on A1


    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify szradm list-roles
        When I run "szradm list-roles" on A1
        And I run "szradm list-roles" on A2
        Then I compare the obtained results of A1,A2
        And Table contains external-ip servers A1,A2

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
        And Table contains external-ip servers A1,A2

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify szradm list-roles --behaviour app
        When I run "szradm list-roles --behaviour app" on A1
        And I run "szradm list-roles --behaviour app" on A2
        Then I compare the obtained results of A1,A2
        And Table contains external-ip servers A1,A2

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify szradm list-virtualhosts


    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify szradm get-https-certificate


    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify szradm get-ebs-mountpoints


    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify szradm list-messages

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify szradm message-details


    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify szradm fire-event

