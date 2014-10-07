Using step definitions from: steps/common_api_steps, steps/apache_api_steps
Feature: Apache application server role, api tests

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstraping apache role
        Given I have a an empty running farm
        When I add app role to this farm
        Then I expect server bootstrapping as A1
        And scalarizr version is last in A1
        And apache is running on A1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Running methods of changing the status of the service
        Given apache is running on A1
        Then I run "ApacheApi" command "configtest" on A1
        Then I run "ApacheApi" command "stop_service" and pid has been changed on A1 with arguments:
            | reason                               |
            | Apache api method: stop_service test |
        And scalarizr debug log in A1 contains 'Apache api method: stop_service test'
        Then I run "ApacheApi" command "start_service" and pid has been changed on A1
        When I run "ApacheApi" command "get_webserver_statistics" on A1
        And api result "get_webserver_statistics" has "Uptime" data
        And not ERROR in A1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Creates a name-based plain-text apache virtual host
        Given I run "ApacheApi" command "create_vhost" on A1 with arguments:
            | hostname        | port | template            | ssl    | reload |
            | www.example.com | 80   | NAME-BASED-TEMPLATE | False  | True   |
        And api result "create_vhost" contain argument "hostname"
        Then I run "ApacheApi" command "list_served_virtual_hosts" on A1
        And api result "list_served_virtual_hosts" contain argument "hostname" from command "create_vhost"
        When I run "ApacheApi" command "reconfigure" on A1 with arguments:
            | vhosts            | reload | rollback_on_error |
            | RECONFIGURE-VHOST | True   | False             |
        When I run "ApacheApi" command "list_served_virtual_hosts" on A1
        And api result "list_served_virtual_hosts" does not contain argument "hostname" from command "create_vhost"
        Then I run "ApacheApi" command "reload_service" on A1 with arguments:
            | reason                                 |
            | Apache api method: reload_service test |
        And scalarizr debug log in A1 contains 'Apache api method: reload_service test'
        When I run "ApacheApi" command "update_vhost" on A1 with arguments:
            | signature                           | hostname                | port |
            | ("www.reconfigure-example.com", 80) | www.updated-example.com | 80   |
        When I run "ApacheApi" command "list_served_virtual_hosts" on A1
        And api result "list_served_virtual_hosts" contain argument "hostname" from command "update_vhost"
        When I run "ApacheApi" command "delete_vhosts" on A1 with arguments:
            | vhosts                             | reload |
            | [("www.updated-example.com", 80),] | True   |
        When I run "ApacheApi" command "list_served_virtual_hosts" on A1
        And api result "list_served_virtual_hosts" does not contain argument "vhosts" from command "delete_vhosts"
        Then I run "ApacheApi" command "restart_service" and pid has been changed on A1 with arguments :
            | reason                                  |
            | Apache api method: restart_service test |
        And scalarizr debug log in A1 contains 'Apache api method: restart_service test'
        And apache is running on A1
        And not ERROR in A1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Creates a name-based apache virtual host with ssl support
        Given I run "ApacheApi" command "create_vhost" on A1 with arguments:
            | hostname                   | port  | template                | ssl    | ssl_certificate_id | reload |
            | www.secure.example.com     | 443   | SSL-NAME-BASED-TEMPLATE | True   | 801                | True   |
        And api result "create_vhost" contain argument "hostname"
        Then I run "ApacheApi" command "set_default_ssl_certificate" on A1 with arguments:
            | id  |
            | 801 |
        Then I run "ApacheApi" command "list_served_virtual_hosts" on A1
        And api result "list_served_virtual_hosts" contain argument "hostname" from command "create_vhost"
        When I run "ApacheApi" command "reconfigure" on A1 with arguments:
            | vhosts                | reload | rollback_on_error |
            | RECONFIGURE-SSL-VHOST | True   | False             |
        When I run "ApacheApi" command "list_served_virtual_hosts" on A1
        And api result "list_served_virtual_hosts" does not contain argument "hostname" from command "create_vhost"
        Then I run "ApacheApi" command "reload_service" on A1 with arguments:
            | reason                                     |
            | Apache api method: reload_service ssl test |
        And scalarizr debug log in A1 contains 'Apache api method: reload_service ssl test'
        When I run "ApacheApi" command "update_vhost" on A1 with arguments:
            | signature                                   | hostname                       | port |
            | ("www.reconfigure-secure.example.com", 443) | www.updated-secure.example.com | 443  |
        When I run "ApacheApi" command "list_served_virtual_hosts" on A1
        And api result "list_served_virtual_hosts" contain argument "hostname" from command "update_vhost"
        When I run "ApacheApi" command "delete_vhosts" on A1 with arguments:
            | vhosts                                     | reload |
            | [("www.updated-secure.example.com", 443),] | True   |
        When I run "ApacheApi" command "list_served_virtual_hosts" on A1
        And api result "list_served_virtual_hosts" does not contain argument "vhosts" from command "delete_vhosts"
        Then I run "ApacheApi" command "restart_service" and pid has been changed on A1 with arguments :
            | reason                                      |
            | Apache api method: restart_service ssl test |
        And scalarizr debug log in A1 contains 'Apache api method: restart_service ssl test'
        And apache is running on A1
        And not ERROR in A1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Disable SSL on website
        Given I create domain D1
        And I add ssl virtual host with key revizor-key to domain D1 on A1
        And D1 resolves into A1 ip address
        Then I run "ApacheApi" command "list_served_virtual_hosts" on A1
        And api result "list_served_virtual_hosts" contain argument "hostname" from command "create_vhost"
        And domain D1 contain default https web page on A1
        Then I update virtual host on domain D1 from ssl to plain-text on A1
        Then I run "ApacheApi" command "list_served_virtual_hosts" on A1
        And api result "list_served_virtual_hosts" contain argument "hostname" from command "update_vhost"
        And domain D1 contain default http web page on A1
        And not ERROR in A1 scalarizr log
