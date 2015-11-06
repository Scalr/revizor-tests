Using step definitions from: steps/new_pkg_update_steps, steps/import_steps, steps/lifecycle_steps, steps/scripting_steps
Feature: Update scalarizr windows test

    @bootstrap @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Update at bootstrap windows test, new role create
      Given I have a server running in cloud
      When I install scalarizr to the server
      Then I create image from deployed server
      And I add image to the new role

    @bootstrap  @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Update at bootstrap windows test, use new role
      Given I have a an empty running farm
      And I add created role to the farm
      When I expect server bootstrapping as M2
      Then scalarizr version is valid in M2
      When I execute script 'Windows ping-pong. CMD' synchronous on M2
      And I see script result in M2
      And script output contains 'pong' in M2

    @ui @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Update by Scalr UI
      Given I have running server M2
      Then I change branch to test-branch for role
      When I trigger scalarizr update by Scalr UI
      Then scalarizr version is valid in M2
      Then I execute script 'Test script name' synchronous on M2
      And I see script result in M2
      Then I checkout to test-branch from branch tested-branch
      And I change branch to test-branch for role
      When I trigger scalarizr update by Scalr UI
      Then scalarizr version is valid in M2
      Then I execute script 'Test script name' synchronous on M2
      And I see script result in M2



