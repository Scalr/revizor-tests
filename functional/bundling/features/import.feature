Feature: Import server to scalr and use this role

    Scenario: Executing import command
        Given I have a server running in cloud
        When I execute on it import command
        Then Scalr receives Hello
        And bundle task was created

    Scenario: Using new role
        Given I have a an empty running farm
        And bundle task becomes completed
        When I add to farm imported role
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
