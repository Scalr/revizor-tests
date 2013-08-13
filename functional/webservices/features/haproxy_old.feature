Feature: HAProxy load balancer role

    Scenario: Bootstraping app role
        Given I have a an empty running farm
        When I add app role to this farm
        Then I expect server bootstrapping as A1 in app role
        And apache is running on A1

    Scenario: Adding haproxy to upstream
        When I add haproxy role proxying http 80 port to app role
        Then I expect server bootstrapping as H1 in haproxy role
        And H1 have A1 in backends
        And process haproxy is running in H1

    Scenario: Load balancing
       When I increase minimum servers to 2 for app role
       Then I expect server bootstrapping as A2 in app role
       And H1 have A2 in backends
       And process haproxy is running in H1

    Scenario: Removing app server
        When I terminate server A1 with decrease
        And H1 not have A1 in backends
        But H1 have A2 in backends
        And process haproxy is running in H1

    Scenario: HTTP proxying
        When I add virtual host D1
        Then D1 resolves into H1 ip address
        And http get D1 matches D1 index page in A2
        And process haproxy is running in H1