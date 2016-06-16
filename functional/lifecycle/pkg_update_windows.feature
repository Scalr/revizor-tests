Using step definitions from: steps/pkg_update_steps, steps/import_steps, steps/lifecycle_steps, steps/scripting_steps, steps/new_szr_upd_system
Feature: Windows update for new package test

    @ec2 @gce
    Scenario: Update from stable to branch on startup
        Given I have a clean image
        And I add image to the new role
        Given I have a an empty running farm
        And I add created role to the farm
        When I see pending server M1
        Then I install scalarizr to the server M1 from the branch stable
        And I reboot hard server M1
        When I expect server bootstrapping as M1
        Then scalarizr version was updated in M1
        When I execute script 'Windows ping-pong. CMD' synchronous on M1
        And I see script result in M1
        And script output contains 'pong' in M1

    @ec2 @gce
    Scenario: Update from latest to branch on startup
        Given I have a clean image
        And I add image to the new role
        Given I have a an empty running farm
        And I add created role to the farm
        When I see pending server M2
        Then I install scalarizr to the server M2 from the branch latest
        And I reboot hard server M2
        When I expect server bootstrapping as M2
        Then scalarizr version was updated in M2
        When I execute script 'Windows ping-pong. CMD' synchronous on M2
        And I see script result in M2
        And script output contains 'pong' in M2

    @ec2 @gce
    Scenario: Update from stable to branch from ScalrUI
        Given I have a clean and stopped farm
        And I add role to this farm with branch_stable
        When I start farm
        Then I see pending server M3
        And I wait and see running server M3
        And scalarizr version from stable is last in M3
        When I change branch to system for role
        And I trigger scalarizr update by Scalr UI on M3
        Then update process is finished on M3 with status completed
        And Scalr receives HostUpdate from M3
        And scalarizr version from system is last in M3
        When I execute script 'Windows ping-pong. CMD' synchronous on M3
        And I see script result in M3
        And script output contains 'pong' in M3

    @ec2 @gce
    Scenario: Update from latest to branch from ScalrUI
        Given I have a clean and stopped farm
        And I add role to this farm with branch_latest
        When I start farm
        Then I see pending server M4
        And I wait and see running server M4
        And scalarizr version from latest is last in M4
        When I change branch to system for role
        And I trigger scalarizr update by Scalr UI on M4
        Then update process is finished on M4 with status completed
        And Scalr receives HostUpdate from M4
        And scalarizr version from system is last in M4
        When I execute script 'Windows ping-pong. CMD' synchronous on M4
        And I see script result in M4
        And script output contains 'pong' in M4

    @ec2 @gce
    Scenario: Update from branch to stable
        Given I have a clean image
        And I add image to the new role
        When I have a an empty running farm
        Then I add created role to the farm with branch_stable
        And I see pending server M5
        Then I install scalarizr to the server M5
        And I reboot hard server M5
        When I expect server bootstrapping as M5
        Then scalarizr version was updated in M5
        When I execute script 'Windows ping-pong. CMD' synchronous on M5
        And I see script result in M5
        And script output contains 'pong' in M5

    @ec2 @gce
    Scenario: Update from stable to branch on startup and new package
        Given I have a clean image
        And I add image to the new role
        Given I have a an empty running farm
        And I add created role to the farm
        When I see pending server M6
        Then I install scalarizr to the server M6 from the branch stable
        And I reboot hard server M6
        When I expect server bootstrapping as M6
        Then scalarizr version was updated in M6
        Then I have a copy of the system branch
        When I wait for new package was built
        And I trigger scalarizr update by Scalr UI on M6
        Then update process is finished on M6 with status completed
        When I execute script 'Windows ping-pong. CMD' synchronous on M6
        And I see script result in M6
        And script output contains 'pong' in M6