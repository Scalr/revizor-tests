Using step definitions from: steps/common_api_steps, steps/apache_api_steps
Feature: Apache application server role, api tests

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstraping apache role
        Given I have a an empty running farm
        When I add app role to this farm
        Then I expect server bootstrapping as A1
        And scalarizr version is last in A1
        And apache is running on A1
        And http get A1 contains default welcome message

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Launch base apache api method
        Given apache is running on A1
        When I run "ApacheApi" command "configtest" on A1
        When I run "ApacheApi" command "reload_service" on A1 with arguments:
            | reason                                  |
            | Apache api method "reload_service" test |
        When I run "ApacheApi" command "restart_service" on A1 with arguments:
            | reason                                   |
            | Apache api method "restart_service" test |
        When I run "ApacheApi" command "stop_service" on A1 with arguments:
            | reason                                |
            | Apache api method "stop_service" test |
        When I run "ApacheApi" command "start_service" on A1 with arguments:
            | reason                                 |
            | Apache api method "start_service" test |
        Then apache is running on A1
        When I run "ApacheApi" command "set_default_ssl_certificate" on A1 with arguments:
            | id  |
            | 801 |
        When I run "ApacheApi" command "get_webserver_statistics" on A1
        And not ERROR in A1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Creates a name-based apache virtual host without ssl support
        Given I run "ApacheApi" command "create_vhost" on A1 with arguments:
            | hostname        | port | template            | ssl    | reload |
            | www.example.com | 80   | NAME-BASED-TEMPLATE | FALSE  | TRUE   |
        And api result "create_vhost" has argument "hostname"
        When I run "ApacheApi" command "reconfigure" on A1 with arguments:
            | vhosts            | reload | rollback_on_error | async |
            | RECONFIGURE-VHOST | TRUE   | TRUE              | TRUE  |
        When I run "ApacheApi" command "list_served_virtual_hosts" on A1
        And api result "list_served_virtual_hosts" has argument "hostname"
        When I run "ApacheApi" command "update_vhost" on A1 with arguments:
            | signature              | hostname                | port |
            | VHOST-UPDATE-SIGNATURE | www.example-updated.com | 80   |
        When I run "ApacheApi" command "list_served_virtual_hosts" on A1
        And api result "list_served_virtual_hosts" has argument "hostname"
        When I run "ApacheApi" command "delete_vhosts" on A1 with arguments:
            | vhosts                 | reload |
            | VHOST-DELETE-SIGNATURE | TRUE   |
        When I run "ApacheApi" command "list_served_virtual_hosts" on A1
        And api result "list_served_virtual_hosts" has not argument "vhosts"
        And not ERROR in A1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Creates a name-based apache virtual host with ssl support
        Given I run "ApacheApi" command "create_vhost" on A1 with arguments:
            | hostname                   | port  | template                | ssl    | ssl_certificate_id | reload |
            | www.secure.example.com     | 443   | SSL-NAME-BASED-TEMPLATE | TRUE   | 801                | TRUE   |
        And api result "create_vhost" has argument "hostname"
        When I run "ApacheApi" command "reconfigure" on A1 with arguments:
            | vhosts                | reload | rollback_on_error | async |
            | RECONFIGURE-SSL-VHOST | TRUE   | TRUE              | TRUE  |
        When I run "ApacheApi" command "list_served_virtual_hosts" on A1
        And api result "list_served_virtual_hosts" has argument "hostname"
        When I run "ApacheApi" command "update_vhost" on A1 with arguments:
            | signature                  | hostname                       | port  |
            | VHOST-SSL-UPDATE-SIGNATURE | www.secure.example-updated.com | 443   |
        When I run "ApacheApi" command "list_served_virtual_hosts" on A1
        And api result "list_served_virtual_hosts" has argument "hostname"
        When I run "ApacheApi" command "delete_vhosts" on A1 with arguments:
            | vhosts                     | reload |
            | VHOST-SSL-DELETE-SIGNATURE | TRUE   |
        When I run "ApacheApi" command "list_served_virtual_hosts" on A1
        And api result "list_served_virtual_hosts" has not argument "vhosts"
        And not ERROR in A1 scalarizr log