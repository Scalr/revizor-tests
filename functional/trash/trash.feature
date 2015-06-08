Feature: Some basic steps
    

    Scenario: Add role, run and terminate
        Given I have a clean and stopped farm
        When I add base role to this farm
        And I run the farm
        Then the farm is running
        