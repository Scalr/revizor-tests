Using step definitions from: steps/new_pkg_update_steps, steps/import_steps, steps/lifecycle_steps, steps/scripting_steps, steps/new_szr_upd_system,
Feature: Update scalarizr windows test

    @ui @ec2 @gce
    Scenario Outline: Update from Scalr UI, windows test
      Given I have manually installed scalarizr '<default_agent>' on M1
      And scalarizr version is default in M1
      When I change branch for role
      Then I trigger scalarizr update by Scalr UI on M1
      And update process is finished on M1 with status completed
      Then Scalr receives HostUpdate from M1
      And scalarizr version from role is last in M1
      When I execute script 'Windows ping-pong. CMD' synchronous on M1
      Then I see script result in M1
      And script output contains 'pong' in M1

    Examples:
      | default_agent |
      | 3.8.5         |
      | 3.12.7        |


    @manual @ec2 @gce
    Scenario Outline: Manual scalarizr update, windows test
      Given I have manually installed scalarizr '<default_agent>' on M2
      And scalarizr version is default in M2
      When I install new scalarizr to the server M2 manually
      Then update process is finished on M2 with status completed
      Then Scalr receives HostUpdate from M2
      And scalarizr version from role is last in M2
      When I execute script 'Windows ping-pong. CMD' synchronous on M2
      Then I see script result in M2
      And script output contains 'pong' in M2

    Examples:
      | default_agent |
      | 3.8.5         |
      | 3.12.7        |


    @ui @rollback @ec2 @gce
    Scenario Outline: Update from Scalr UI to corrupted package, Windows test
      Given I have manually installed scalarizr '<default_agent>' on M3
      And scalarizr version is default in M3
      When I build corrupted package
      Then I set branch with corrupted package for role
      Then I trigger scalarizr update by Scalr UI on M3
      And update process is finished on M3 with status rollbacked
      And scalarizr version is default in M3
      When I execute script 'Windows ping-pong. CMD' synchronous on M3
      Then I see script result in M3
      And script output contains 'pong' in M3

    Examples:
      | default_agent |
      | 3.8.5         |
      #| 3.12.7        |