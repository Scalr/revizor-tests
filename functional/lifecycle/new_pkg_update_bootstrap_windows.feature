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


    @bootstrap @ui @msi_new @ec2 @gce
    Scenario: Update to corrupt package after bootstrap windows test, no prev updates
      Given I have a server running in cloud
      When I install scalarizr with sysprep to the server manually
      Then I create image from deployed server
      And I add image to the new role


    @bootstrap @ui @msi_new @ec2 @gce @allow_clean_data
    Scenario: Update to corrupt package after bootstrap windows test, no prev updates
      Given I have a an empty running farm
      And I add created role to the farm
      And I change branch for role
      When I expect server bootstrapping as M3
      And scalarizr version from role is last in M3
      When I build corrupt package
      And I set branch with corrupt package for role
      And I trigger scalarizr update by Scalr UI on M3
      Then update process is finished on M3 with status error
      And scalarizr is not running on M3
      And scalr-upd-client is running on M3


    @bootstrap @ui @msi_new @rollback @ec2 @gce
    Scenario: Update to corrupt package with rollback, windows test
      Given I have a server running in cloud
      When I install scalarizr with sysprep to the server manually
      Then I create image from deployed server
      And I add image to the new role


    @bootstrap @ui @msi_new @rollback @ec2 @gce @allow_clean_data
    Scenario: Update to corrupt package with rollback, windows test
      Given I have a an empty running farm
      And I add created role to the farm
      And I change branch for role
      When I expect server bootstrapping as M4
      And scalarizr version from role is last in M4
      When I build new package
      And I set branch with new package for role
      When I trigger scalarizr update by Scalr UI on M4
      Then update process is finished on M4 with status completed
      And Scalr receives HostUpdate from M4
      And scalarizr version from role is last in M4
      When I build corrupt package
      And I set branch with corrupt package for role
      When I trigger scalarizr update by Scalr UI on M4
      Then update process is finished on M4 with status rollbacked
      And scalarizr is running on M4
      And scalr-upd-client is running on M4
      When I execute script 'Windows ping-pong. CMD' synchronous on M4
      Then I see script result in M4
      And script output contains 'pong' in M4