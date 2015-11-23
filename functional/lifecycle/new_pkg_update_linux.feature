Using step definitions from: steps/new_pkg_update_steps, steps/import_steps, steps/lifecycle_steps, steps/scripting_steps
Feature: Update scalarizr linux test

    @bootstrap @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Update at bootstrap linux test, new role create
      Given I have a clean image
      And I add image to the new role

    @bootstrap @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Update at bootstrap  linux test, use new role
      Given I have a an empty running farm
      And I add created role to the farm
      When I see pending server M1
      Then I install scalarizr to the server M1
      And I reboot server
      When I expect server bootstrapping as M2
      Then scalarizr version is valid in M2
      When I execute script 'Linux ping-pong' synchronous on M2
      And I see script result in M2

    @ui @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Update by Scalr UI
      Given I have running server M2
      Then I change branch to test-branch for role
      When I trigger scalarizr update by Scalr UI
      Then scalarizr version is valid in M2
      Then I execute script 'Revizor update test lin' synchronous on M2
      And I see script result in M2
      Then I checkout to test-branch from branch tested-branch
      And I change branch to test-branch for role
      When I trigger scalarizr update by Scalr UI
      Then scalarizr version is valid in M2
      Then I execute script 'Revizor update test lin' synchronous on M2
      And I see script result in M2



