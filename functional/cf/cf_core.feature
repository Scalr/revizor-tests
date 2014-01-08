Feature: Cloudfoundry application server role test
 
    Scenario: Bootstraping cloudfoundry farm
        Given I have a an empty running farm
        When I add www, cf_dea, cf_router, cf_cloud_controller roles to this farm
        Then I expect server role www bootstrapping as A1
        And I expect server role cf_cloud_controller bootstrapping as C1
        And scalarizr version is last in C1
        And I expect server role cf_router bootstrapping as C2
        And scalarizr version is last in C2
        And I expect server role cf_dea bootstrapping as C3
        And scalarizr version is last in C3
        And cf works in C1

    Scenario: Deploy web application
        When I add domain D1 to A1
        And D1 resolves into A1 ip address
        Then I add vmc user in C1
        And I add test app to C1
        And http get D1 matches D1 index page

    Scenario: DEA repair
        When I terminate server C3
        Then I expect server role cf_dea bootstrapping as C4
        And http get D1 matches D1 index page
        And scalarizr version is last in C4

    Scenario: Router repair
        When I terminate server C2
        Then I expect server role cf_router bootstrapping as C5
        And http get D1 matches D1 index page
        And scalarizr version is last in C5

    Scenario: Controller repair
        When I terminate server C1
        Then I expect server role cf_cloud_controller bootstrapping as C6
        And http get D1 matches D1 index page
        And scalarizr version is last in C6
