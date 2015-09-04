Using step definitions from: steps/new_pkg_update_steps, steps/import_steps
Feature: Update scalarizr test

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Update at bootstrap, new role create
      Given I have a server running in cloud
      When I install scalarizr to the server
      Then I create image
      Then I add image to the new role

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Update at bootstrap, use new role
      Given I have a clean and stopped farm
      And I add created role to the farm
      When I expect server bootstrapping as M1
      Then scalarizr version is valid in M1
      And update-client version is valid in M1
      When I execute script 'Test script name' synchronous on M1
      And I see script result in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Update by Scalr UI
      Given I have running server M1
      Then I change branch to test-branch for role
      When I trigger scalarizr update by Scalr UI
      Then scalarizr version is valid in M1
      Then update-client version is valid in M1
      Then I execute script 'Test script name' synchronous on M1
      And I see script result in M1
      Then I fork tested branch to test-branch
      And I change branch to test-branch for role
      When I trigger scalarizr update by Scalr UI
      Then scalarizr version is valid in M1
      Then update-client version is valid in M1
      Then I execute script 'Test script name' synchronous on M1
      And I see script result in M1



