Using step definitions from: steps/new_pkg_update_steps, steps/import_steps, steps/lifecycle_steps, steps/scripting_steps, steps/new_szr_upd_system
Feature: Update scalarizr linux test

    @bootstrap @ec2 @gce @allow_clean_on_fail
    Scenario: Update at bootstrap linux test, new role create
      Given I have a clean image
      And I add image to the new role

    @bootstrap @ec2 @gce @allow_clean_on_fail
    Scenario: Update at bootstrap linux test, use new role
      Given I have a an empty running farm
      And I add created role to the farm
      When I see pending server M1
      Then I install scalarizr to the server M1
      And I reboot server
      When I expect server bootstrapping as M2
      Then scalarizr version was updated in M2
      When I execute script 'Linux ping-pong' synchronous on M2
      And I see script result in M2

    @ui @ec2 @gce @allow_clean_data
    Scenario: Update from Scalr UI
      Given I have running server M2
      And I save current Scalr update client version on M2
      When I build new package
      And I set branch with new package for role
      And I trigger scalarizr update by Scalr UI on M2
      Then update process is finished on M2 with status completed
      And Scalr receives HostUpdate from M2
      And I check current Scalr update client version was changed on M2
      When I execute script 'Windows ping-pong. CMD' synchronous on M2
      Then I see script result in M2
      And script output contains 'pong' in M2
