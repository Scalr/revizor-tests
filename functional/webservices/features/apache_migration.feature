Feature: Apache application server migration test

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstraping apache role
        Given I have a clean and stopped farm
        And I add app role to this farm with branch_stable
        Then I create domain D1 to app role
        And I add virtual host H1 to app role and domain D1
        Then I create domain D2 to app role
        And I add ssl virtual host H2 to app role and domain D2
        When I start farm
        Then I expect server bootstrapping as A1
        And scalarizr version is last in A1
        And apache is running on A1
        And http get A1 contains default welcome message

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify apache configuration
        When D1 resolves into A1 ip address
        And A1 has H1 in virtual hosts configuration
        Then http get domain D1 matches H1 index page
        When D2 resolves into A1 ip address
        And A1 has H2 in virtual hosts configuration
        Then https get domain D2 matches H1 index page

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Update scalarizr in server
        When I change repo in A1
        And pin new repo in A1
        And update scalarizr in A1
        And scalarizr version is last in A1

