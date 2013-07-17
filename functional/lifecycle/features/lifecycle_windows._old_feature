Feature: Windows server lifecycle
    In order to manage server lifecycle
    As a scalr user
    I want to be able to monitor server state changes

    Scenario: Bootstraping
        Given I have a clean and stopped farm
        And I add role to this farm
        When I launch the farm
        Then I see pending server
        And I wait and see initializing server
        And I wait and see running server
    
    Scenario: Windows reboot
        Given I have running windows server
        When I reboot it
        Then Scalr receives Win_HostDown
        And Scalr receives RebootFinish
        
    Scenario: Execute script on Windows
        Given I have running windows server
        When I execute on it script 'Windows ping-pong'
        Then I see execution result in scripting log
        And script output contains 'pong'