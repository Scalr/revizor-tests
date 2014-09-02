Using step definitions from: steps/bundling_steps
Feature: Bundling server test

    @scalr
    Scenario: Add first role
        Given I have a an empty running farm
        When I add role to this farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1

    @scalr
    Scenario: Create new role
        When I create server snapshot for M1
        Then Bundle task created for M1
        And Bundle task becomes completed for M1

    @scalr
    Scenario: Role should be usable
        Given I have a an empty running farm
        When I add to farm role created by last bundle task
        Then I expect server bootstrapping as M2
        And scalarizr version is last in M2
        And not ERROR in M2 scalarizr log

    @api
    Scenario: Create role via scalarizr api
        Then I create server snapshot for M2 via scalarizr api
        And not ERROR in M2 scalarizr log

    @api
    Scenario: Save new image in role
        Given I have a new image id
        Then I create new role with this image id as R1

    @api
    Scenario: Role created by api should be usable
        Given I have a an empty running farm
        When I add to role R1 to this farm
        Then I expect server bootstrapping as M3
        And scalarizr version is last in M3
        And not ERROR in M3 scalarizr log

