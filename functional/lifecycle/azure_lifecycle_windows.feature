Using step definitions from: steps/common_steps, steps/windows_steps, steps/lifecycle_steps, steps/scripting_steps
Feature: Windows server lifecycle in Azure
    In order to manage server lifecycle
    As a scalr user
    I want to be able to monitor server state changes

    @azure
    Scenario: Bootstraping
        Given I have a clean and stopped farm
        And I add role to this farm
        When I start farm
        Then I see pending server M1
        And I wait and see running server M1
        And scalarizr version is last in M1

#    @azure
#    Scenario: Restart scalarizr by script
#        Given I have running server M1
#        When I execute script 'windows restart scalarizr' synchronous on M1
#        And scalarizr is running on M1
#        And I see script result in M1
#        And script result contains 'Stopping Scalarizr; Stopped!; Starting Scalarizr; Started!' on M1

    @azure
    Scenario: Windows reboot
        When I reboot server M1
        Then Scalr receives Win_HostDown from M1
        And Scalr receives RebootFinish from M1
        And Scalr sends RebootFinish to M1
        And scalarizr is running on M1

    @azure
    Scenario Outline: Scripts executing on Windows
        Given I have running server M1
        When I execute '<script_type>' '<script_name>' '<execute_type>' on M1
        And I see script result in M1
        And script result contains '<output>' on M1

        Examples:
            | script_name            | execute_type | script_type | output                 |
            | Windows ping-pong. CMD | synchronous  |             | pong                   |
            | Windows ping-pong. CMD | asynchronous |             | pong                   |
            | Windows ping-pong. PS  | synchronous  |             | pong                   |
            | Windows ping-pong. PS  | asynchronous |             | pong                   |
            | https://goo.gl/CFeoPC  | asynchronous | local       | Script runned from URL |

    @azure
    Scenario: Restart farm
        When I stop farm
        And wait all servers are terminated
        Then I start farm
        And I expect server bootstrapping as M1
