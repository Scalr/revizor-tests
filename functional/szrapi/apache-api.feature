Using step definitions from: steps/common_api_steps
Feature: Apache application server role, api tests

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstraping apache role
        Given I have a an empty running farm
        When I add app role to this farm
        Then I expect server bootstrapping as A1
        And scalarizr version is last in A1
        And apache is running on A1
        And http get a1 contains default welcome message

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Creates a name-based apache virtual host without ssl support
        Given I run ApacheApi command create_vhost on A1 with arguments:
            | hostname        | port | template            | ssl   | reload |
            | www.example.com | 80   | NAME-BASED-TEMPLATE | false | true   |
        And api result "create_vhost" has argument hostname
        When I run ApacheApi command list_served_virtual_hosts on A1
        And api result "list_served_virtual_hosts" has argument hostname
        When I run ApacheApi command update_vhost on A1 with arguments:
            | signature               | hostname                | port |
            | ('www.example.com', 80) | www.example-updated.com | 80   |
        When I run ApacheApi command list_served_virtual_hosts on A1
        And api result "list_served_virtual_hosts" has argument hostname
        When I run ApacheApi command delete_vhosts on A1 with arguments:
            | vhosts                              | reload |
            | [('www.example-updated.com', 80), ] | True   |
        When I run ApacheApi command list_served_virtual_hosts on A1
        And api result "list_served_virtual_hosts" has not argument vhosts

