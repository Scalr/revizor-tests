Using step definitions from: steps/new_pkg_update_steps, steps/import_steps, steps/lifecycle_steps, steps/scripting_steps, steps/new_szr_upd_system
Feature: Update scalarizr linux test

    @ui @ec2 @gce
    Scenario: Update from Scalr UI
      Given I have a clean and stopped farm
      And I add role to this farm
      When I start farm
      Then I see pending server M1
      And I wait and see running server M1
      And scalarizr version is last in M1
      When I change branch for role
      And I trigger scalarizr update by Scalr UI on M1
      Then update process is finished on M1 with status completed
      And Scalr receives HostUpdate from M1
      And scalarizr version from role is last in M1
      When I execute script 'Linux ping-pong' synchronous on M1
      And I see script result in M1
      And script output contains 'pong' in M1

    @bootstrap @ec2 @gce @allow_clean_on_fail
    Scenario: Update at bootstrap linux test, new role create
      Given I have a clean image
      And I add image to the new role

    @bootstrap @ec2 @gce @allow_clean_on_fail
    Scenario: Update at bootstrap linux test, use new role
      Given I have a an empty running farm
      And I add created role to the farm
      When I see pending server M2
      Then I install scalarizr to the server M2
      And I reboot server
      When I expect server bootstrapping as M3
      Then scalarizr version was updated in M3
      When I execute script 'Linux ping-pong' synchronous on M3
      And I see script result in M3
      And script output contains 'pong' in M3

    @ui @ec2 @gce @allow_clean_data
    Scenario: Update from Scalr UI to new package
      Given I have running server M3
      And I save current Scalr update client version on M3
      When I build new package
      And I set branch with new package for role
      And I trigger scalarizr update by Scalr UI on M3
      Then update process is finished on M3 with status completed
      And Scalr receives HostUpdate from M3
      And I check current Scalr update client version was changed on M3
      When I execute script 'Linux ping-pong' synchronous on M3
      Then I see script result in M3
      And script output contains 'pong' in M3
