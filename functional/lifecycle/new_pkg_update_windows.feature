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
    Scenario Outline: Manual scalarizr update, Windows test
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
    Scenario: Update from Scalr UI to corrupt package with rollback, Windows test
      Given I have manually installed scalarizr '3.8.5' on M3
      And scalarizr version is default in M3
      When I build corrupt package
      Then I set branch with corrupt package for role
      Then I trigger scalarizr update by Scalr UI on M3
      And update process is finished on M3 with status rollbacked
      And scalarizr version is default in M3
      When I execute script 'Windows ping-pong. CMD' synchronous on M3
      Then I see script result in M3
      And script output contains 'pong' in M3


    @ui @rollback @ec2 @gce
    Scenario: Update from Scalr UI after rollback, Windows test
      Given I have manually installed scalarizr '3.8.5' on M4
      And scalarizr version is default in M4
      When I build corrupt package
      Then I set branch with corrupt package for role
      Then I trigger scalarizr update by Scalr UI on M4
      And update process is finished on M4 with status rollbacked
      And scalarizr version is default in M4
      When I change branch for role
      Then I trigger scalarizr update by Scalr UI on M4
      And update process is finished on M4 with status completed
      Then Scalr receives HostUpdate from M4
      And scalarizr version from role is last in M4
      When I execute script 'Windows ping-pong. CMD' synchronous on M4
      Then I see script result in M4
      And script output contains 'pong' in M4


    @manual @rollback @ec2 @gce
    Scenario: Manual scalarizr update to corrupt package with rollback, Windows test
      Given I have manually installed scalarizr '3.8.5' on M5
      And scalarizr version is default in M5
      When I build corrupt package
      Then I install corrupt package to the server M5
      And update process is finished on M5 with status rollbacked
      And scalarizr version is default in M5
      When I execute script 'Windows ping-pong. CMD' synchronous on M5
      Then I see script result in M5
      And script output contains 'pong' in M5


    @manual @rollback @ec2 @gce
    Scenario: Manual scalarizr update after rollback, Windows test
      Given I have manually installed scalarizr '3.8.5' on M6
      And scalarizr version is default in M6
      When I build corrupt package
      Then I install corrupt package to the server M6
      And update process is finished on M6 with status rollbacked
      And scalarizr version is default in M6
      When I install new scalarizr to the server M6 manually
      Then update process is finished on M6 with status completed
      Then Scalr receives HostUpdate from M6
      And scalarizr version from role is last in M6
      When I execute script 'Windows ping-pong. CMD' synchronous on M6
      Then I see script result in M6
      And script output contains 'pong' in M6


    @ui @rollback @ec2 @gce
    Scenario: Update from Scalr UI after corrupt package install, Windows test
      Given I have manually installed scalarizr '3.12.7' on M7
      And scalarizr version is default in M7
      When I build corrupt package
      Then I set branch with corrupt package for role
      Then I trigger scalarizr update by Scalr UI on M7
      And update process is finished on M7 with status error
      When I change branch for role
      Then I trigger scalarizr update by Scalr UI on M7
      And update process is finished on M7 with status completed
      Then Scalr receives HostUpdate from M7
      And scalarizr version from role is last in M7
      When I execute script 'Windows ping-pong. CMD' synchronous on M7
      Then I see script result in M7
      And script output contains 'pong' in M7


    @manual @rollback @ec2 @gce
    Scenario: Manual scalarizr update after corrupt package install, Windows test
      Given I have manually installed scalarizr '3.12.7' on M8
      And scalarizr version is default in M8
      When I build corrupt package
      Then I install corrupt package to the server M8
      And update process is finished on M8 with status error
      When I install new scalarizr to the server M8 manually
      Then update process is finished on M8 with status completed
      Then Scalr receives HostUpdate from M8
      And scalarizr version from role is last in M8
      When I execute script 'Windows ping-pong. CMD' synchronous on M8
      Then I see script result in M8
      And script output contains 'pong' in M8