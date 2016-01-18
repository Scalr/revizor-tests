Using step definitions from: steps/new_pkg_update_steps, steps/import_steps, steps/lifecycle_steps, steps/scripting_steps
Feature: Update scalarizr windows test

    @legacy @ui @ec2 @gce
    Scenario: Update from Scalr UI windows test
      Given I have manualy installed scalarizr 'snapshot/3.8.5' on M1
      And I wait and see running server M1
      When I change branch to system for role
      Then I trigger scalarizr update by Scalr UI on M1

    @msi @ui @ec2 @gce
    Scenario: Update from Scalr UI windows test
      Given I have manualy installed scalarizr on M1
      And I wait and see running server M1
      When I change branch for role
      Then I trigger scalarizr update by Scalr UI on M1
