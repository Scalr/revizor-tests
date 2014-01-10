Using step definitions from: steps/common_steps, steps/apache_steps, steps/nginx_steps, steps/nginx_new_steps
Feature: Nginx load balancer role test with apache backends and new proxy settings

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstraping nginx role
        Given I have a an empty running farm
        When I add www role to this farm
        Then I expect server bootstrapping as W1
        And scalarizr version is last in W1
        And nginx is running on W1
        And http get W1 contains 'No running app instances found'

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Adding app to upstream
        When I add app role to this farm
        And bootstrap 2 servers as (A1, A2) in app role
        Then W1 upstream list should contains A1, A2

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Check proxy for role
        When I create domain D1 to www role
        And I add virtual host H1 to app role and domain D1
        And I add http proxy P1 to www role with H1 host to app role with ip_hash
        Then I reboot server W1
        And Scalr receives RebootFinish from W1
        And W1 upstream list should contains A1, A2
        And W1 proxies list should contains H1
        And 'ip_hash' in W1 upstream file
        And nginx is running on W1
        Then D1 resolves into W1 ip address
        And http get domain D1 matches H1 index page

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify new apache server append and deletes to/from backend
        When I increase minimum servers to 3 for app role
        Then I expect server bootstrapping as A3
        And W1 upstream list should contains A1, A2, A3
        Then I force terminate server A3 with decrease
        And Scalr sends HostDown to W1
        And W1 upstream list should not contain A3

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Modify first proxy and check options
        When I modify proxy P1 in www role without ip_hash and proxies:
          """
          keepalive_timeout 10s;
          / A1 default 1 limit_rate 4096;
          / A2 backup 2
          / example.com down
          /custom_port A1:8002 default limit_rate 8192;
          """
        Then I reboot server W1
        When Scalr receives RebootFinish from W1
        And 'A1 default weight=1' in W1 upstream file
        And 'A1:8002 default' in W1 upstream file
        And 'A2 backup weight=2' in W1 upstream file
        And 'example.com down' in W1 upstream file
        And 'limit_rate 4096;' in W1 proxies file
        And 'limit_rate 8192;' in W1 proxies file
        And nginx is running on W1
        Then I start BaseHttpServer on 8002 port in A1
        And http get domain D1/custom_port matches 'It works!'
        And http get domain D1 matches H1 index page

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Testing proxy delete
        When I delete proxy P1 in www role
        Then I reboot server W1
        And Scalr receives RebootFinish from W1
        Then W1 upstream list should be clean
        And process nginx is running in W1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Add two SSL domains
        When I create domain D2 to www role
        And I add virtual host H2 to app role and domain D2
        And I add http/https proxy P2 to www role with H2 host to app role
        When I create domain D3 to www role
        And I add virtual host H3 to app role and domain D3
        And I add https proxy P3 to www role with H3 host to app role
        Then I reboot server W1
        And Scalr receives RebootFinish from W1
        Then D2 resolves into W1 ip address
        And https get domain D2 matches H2 index page
        And D2 http redirect to D2 https
        Then D3 resolves into W1 ip address
        And https get domain D3 matches H3 index page
        And D3 http not redirect to D3 https
