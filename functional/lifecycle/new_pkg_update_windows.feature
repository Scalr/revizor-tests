Using step definitions from: steps/new_pkg_update_steps, steps/import_steps, steps/lifecycle_steps, steps/scripting_steps
Feature: Update scalarizr windows test

    @legacy @ui @ec2 @gce
    Scenario: Update from Scalr UI windows test
      Given I have manualy installed scalarizr 'snapshot/3.8.5' on M1
      #When I change branch to test-branch for role
      #Then I trigger scalarizr update by Scalr UIi

      #Given I have a clean image
      #And I add image to the new role
      #When I have a an empty running farm
      #Then I add created role to the farm
      #And I see pending server M1
      #When I install scalarizr to the server
      #Then I forbid scalarizr update at startup and run it on M1
      #And scalarizr version is valid in M2
