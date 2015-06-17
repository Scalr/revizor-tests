Using step definitions from: steps/common_steps, steps/apache_steps, steps/haproxy_steps
Feature: HAProxy load balancer role

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstraping haproxy role
        Given I have a clean and stopped farm
        When I add haproxy role to this farm
        When I add proxy P1 to haproxy role for 80 port with backends: 'example.com default' and healthcheck: 16, 21, 10
        And I start farm
        Then I expect server bootstrapping as W1
        And W1 backend list for 80 port should contains 'example.com default'
        And scalarizr version is last in W1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Testing proxy delete
        When I delete proxy P1 in haproxy role
        Then I reboot server W1
        And Scalr receives RebootFinish from W1
        Then W1 config should not contains P1
        And process haproxy is running in W1
        And 80 port is listen on W1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Adding app to upstream
        When I add app role to this farm
        And bootstrap 2 servers as (A1, A2) in app role

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Check proxy for role
        When I create domain D1 to haproxy role
        And I add virtual host H1 to app role and domain D1
        Then I add proxy P1 to haproxy role for 80 port with app role backend
        When I reboot server W1
        And Scalr receives RebootFinish from W1
        And W1 listen list should contains backend for 80 port
        And W1 backend list for 80 port should contains A1, A2
        And process haproxy is running in W1
        And 80 port is listen on W1
        Then D1 resolves into W1 ip address
        And http get domain D1 matches H1 index page

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify new apache server append and deletes to/from backend
        When I increase minimum servers to 3 for app role
        Then I expect server bootstrapping as A3
        And Scalr sends HostUp to W1
        And W1 backend list for 80 port should contains A1, A2, A3
        Then I force terminate server A3 with decrease
        And Scalr sends HostDown to W1
        And W1 backend list for 80 port should not contains A3
        And http get domain D1 matches H1 index page

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Modify first proxy and check options
        When I modify proxy P1 in haproxy role with backends: 'A1 default' 'A2 backup' 'example.com disabled' and healthcheck: 16, 21, 10
        Then I reboot server W1
        And Scalr receives RebootFinish from W1
        And W1 backend list for 80 port should contains 'A1 default', 'A2 backup', 'example.com disabled'
        And healthcheck parameters is 16, 21, 10 in W1 backend file for 80 port
        And process haproxy is running in W1
        And 80 port is listen on W1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Add second proxy
        When I add proxy P2 to haproxy role for 8000 port with backends: 'A1:8002 default' 'example2.com disabled' 'example3.com backup' and healthcheck: 12, 20, 8
        Then I reboot server W1
        And Scalr receives RebootFinish from W1
        And W1 backend list for 8000 port should contains 'A1:8002 default'
        And W1 backend list for 8000 port should contains 'example2.com disabled'
        And W1 backend list for 8000 port should contains 'example3.com backup'
        And healthcheck parameters is 12, 20, 8 in W1 backend file for 8000 port
        And process haproxy is running in W1
        And 80 port is listen on W1
        When I start BaseHttpServer on 8002 port in A1
        Then 8000 port is listen on W1
        And 8000 get domain D1 matches 'It works!'

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Check network options
        Given I have a clean and stopped farm
        When I add app role to this farm
        And I add haproxy role to this farm
        Then I start farm
        And I expect server bootstrapping as W1
        And bootstrap 1 servers as (A1) in app role
        Then I add proxy P1 to haproxy role for 80 port with app role backend and public network
        And I add proxy P2 to haproxy role for 100 port with app role backend and private network
        When I reboot server W1
        And Scalr receives RebootFinish from W1
        Then W1 listen list should contains backend for 80 port
        And W1 backend list for 80 port should contains A1:public
        And W1 listen list should contains backend for 100 port
        And W1 backend list for 100 port should contains A1:private

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Check templates
        Given I have a clean and stopped farm
        When I add app role to this farm
        And I add haproxy role to this farm
        Then I start farm
        And I expect server bootstrapping as W1
        And bootstrap 1 servers as (A1) in app role
        Then I add proxy P1 to haproxy role for 80 port with app role backend and proxy template and global template
        And I reboot server W1 
        And Scalr receives RebootFinish from W1
        Then W1 listen list should contains P1 proxy template for 80 port