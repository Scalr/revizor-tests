Feature: Nginx load balancer role test with apache backends and new proxy settings

    Scenario: Bootstraping nginx role
        Given I have a an empty running farm
        When I add www role to this farm
        Then I expect server bootstrapping as W1
        And scalarizr version is last in W1
        And nginx is running on W1
        And http get W1 contains 'No running app instances found'

    Scenario: Adding app to upstream
        When I add app role to this farm
        And bootstrap 2 servers as (A1, A2)
        Then W1 upstream list should contains A1, A2
        And http get W1 contains 'If you can see this page, it means that your Scalr farm configured succesfully'

    Scenario: Check proxy for role
        When I add virtual host H1 assigned to app role
        And I add http proxy P1 to www role with H1 host to app role with ip_hash
        Then I reboot server W1
        And Scalr receives RebootFinish from W1
        And W1 upstream list should contains A1, A2
        And W1 proxies list should contains H1
        And 'ip_hash' in W1 upstream file
        And nginx is running on W1
        Then H1 resolves into W1 ip address
        And http get H1 matches H1 index page

    Scenario: Verify new apache server append and deletes to/from backend
        When I increase minimum servers to 3 for app role
        Then I expect server bootstrapping as A3
        And W1 upstream list should contains A1, A2, A3
        Then I force terminate server A3 with decrease
        And Scalr sends HostDown to W1
        And W1 upstream list should not contain A3

    Scenario: Modify first proxy and check options
        When I modify proxy P1 in www role without ip_hash and proxies: 'A1 default' 'A2 backup' 'example.com down'
        Then I reboot server W1
        And Scalr receives RebootFinish from W1
        And 'A1 default' in W1 upstream file
        And 'A2 backup' in W1 upstream file
        And 'example.com down' in W1 upstream file
        And nginx is running on W1

    Scenario: Testing proxy delete
        When I delete proxy P1 in www role
        Then I reboot server W1
        And Scalr receives RebootFinish from W1
        Then W1 upstream list should be clean
        And process nginx is running in W1

    Scenario: Add two SSL domains
        When I add virtual host H2 assigned to app role
        And I add http/https proxy P2 to www role with H2 host to app role
        When I add virtual host H3 assigned to app role
        And I add https proxy P3 to www role with H3 host to app role
        Then I reboot server W1
        And Scalr receives RebootFinish from W1
        Then H2 resolves into W1 ip address
        And https get H2 matches H2 index page
        And H2 http redirect to H2 https
        Then H3 resolves into W1 ip address
        And https get H3 matches H3 index page
        And H3 http not redirect to H3 https
