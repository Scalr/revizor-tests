Using step definitions from: steps/bundling_steps
Feature: Bundling server test
    
    Scenario: Add first role
        Given I have a an empty running farm
        When I add role to this farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
    
    Scenario: Create new role
        Given I have running server
        When I create server snapshot
        Then Bundle task created
        And Bundle task becomes completed
    
    Scenario: Role should be usable
        Given I have a an empty running farm
        When I add to farm role created by last bundle task
        Then I expect server bootstrapping as M2
        And scalarizr version is last in M2
        And not ERROR in M2 scalarizr log

    Scenario: Create role via scalarizr api
        Given I have running server
        Then I create server snapshot via scalarizr api
        And not ERROR in M2 scalarizr log

    Scenario: Save new image in role
        Given I have a new image id
        Then I create new role with this image id

    Scenario: Role created by api should be usable
        Given I have a an empty running farm
        When I add to farm role created by last api bundle task
        Then I expect server bootstrapping as M3
        And scalarizr version is last in M3
        And not ERROR in M3 scalarizr log

