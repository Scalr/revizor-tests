Feature: Build server via rolebuilder and use this role

	Scenario: Build role
        When I start build role
        And Build task started
        Then Build task completed
        And I have new role id

    Scenario: Role should be usable
        Given I have a an empty running farm
        When I add to farm role created by last bundle task
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1