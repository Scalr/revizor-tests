Using step definitions from: steps/new_pkg_update_steps, steps/import_steps, steps/lifecycle_steps, steps/scripting_steps, steps/new_szr_upd_system,
Feature: Update scalarizr windows test

    @legacy @ui @ec2 @gce
    Scenario: Update from Scalr UI windows test
      Given I have manualy installed scalarizr '3.8.5' on M1
      When I change branch to system for role
      Then I trigger scalarizr update by Scalr UI on M1
      And update process is finished on M1 with status completed
      And scalarizr version is valid in M1

    @msi @ui @ec2 @gce
    Scenario: Update from Scalr UI windows test
      Given I have manualy installed scalarizr on M2
      When I change branch for role
      Then I trigger scalarizr update by Scalr UI on M2
      And update process is finished on M2 with status completed
      And scalarizr version is valid in M2
