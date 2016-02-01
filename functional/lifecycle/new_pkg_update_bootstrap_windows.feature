Using step definitions from: steps/new_pkg_update_steps, steps/import_steps, steps/lifecycle_steps, steps/scripting_steps, steps/new_szr_upd_system
Feature: Update scalarizr windows test

    @bootstrap @ec2 @gce
    Scenario: Update at bootstrap windows test, new role create
      Given I have a server running in cloud
      When I install scalarizr with sysprep to the server
      Then I create image from deployed server
      And I add image to the new role

    @bootstrap  @ec2 @gce @allow_clean_data
    Scenario: Update at bootstrap windows test, use new role
      Given I have a an empty running farm
      And I add created role to the farm
      When I expect server bootstrapping as M2
      Then scalarizr version was updated in M2
      When I execute script 'Windows ping-pong. CMD' synchronous on M2
      And I see script result in M2
      And script output contains 'pong' in M2
