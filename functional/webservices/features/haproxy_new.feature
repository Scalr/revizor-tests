Feature: HAProxy load balancer role

    Scenario: Bootstraping haproxy role
        Given I have a an empty running farm
        When I add haproxy role to this farm
        Then I expect server bootstrapping as W1
        And scalarizr version is last in W1

    Scenario: Adding app to upstream
        When I add app role to this farm
        And bootstrap 2 servers as (A1, A2)

    Scenario: Check proxy for role
        When I add virtual host H1 assigned to app role
        And I add proxy P1 to haproxy role for 80 port with app role backend
        Then I reboot server W1
        And Scalr receives RebootFinish from W1
        And W1 backend list for 80 port should contains A1, A2
        And W1 listen list should contains backend for 80 port
        And haproxy process is running on W1
        And 80 port is listen on W1
        Then H1 resolves into W1 ip address
        And http get H1 matches H1 index page

    Scenario: Verify new apache server append and deletes to/from backend
        When I increase minimum servers to 3 for app role
        Then I expect server bootstrapping as A3
        And W1 backend list for 80 port should contains A1, A2, A3
        Then I force terminate server A3 with decrease
        And Scalr sends HostDown to W1
        And W1 backend list for 80 port should not contain A3

    Scenario: Modify first proxy and check options
        When I modify proxy P1 in haproxy role with proxies: 'A1 default' 'A2 backup' 'example.com down' and healthcheck: 16, 21, 10
        Then I reboot server W1
        And Scalr receives RebootFinish from W1
        And W1 backend list for 80 port should contain 'A1 default'
        And W1 backend list for 80 port should contain 'A2 backup'
        And W1 backend list for 80 port should contain 'example.com down'
        And healthcheck parameters is 16, 21, 10 in W1 backend file for 80 port
        And haproxy process is running on W1
        And 80 port is listen on W1

    Scenario: Add second proxy
        When I add proxy P2 to haproxy role for 8000 port with proxies: 'example2.com default' 'example3.com backup' and healthcheck: 12, 20, 8
        Then I reboot server W1
        And Scalr receives RebootFinish from W1
        And W1 backend list for 8000 port should contain 'example2.com default'
        And W1 backend list for 8000 port should contain 'example3.com backup'
        And healthcheck parameters is 12, 20, 8 in W1 backend file for 8000 port
        And haproxy process is running on W1
        And 80 port is listen on W1
        And 8000 port is listen on W1

    Scenario: Testing proxy delete
        When I delete proxy P1 in www role
        Then I reboot server W1
        And Scalr receives RebootFinish from W1
        Then W1 config should be clean
        And haproxy process is running on W1
        And 80 port is not listen on W1
