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
    Scenario: Verify szradm queryenv


    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify szradm list-roles


    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify szradm list-roles by id


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

