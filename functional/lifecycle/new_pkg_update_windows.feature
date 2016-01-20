Using step definitions from: steps/new_pkg_update_steps, steps/import_steps, steps/lifecycle_steps, steps/scripting_steps, steps/new_szr_upd_system,
Feature: Update scalarizr windows test

    @ui @ec2 @gce
    Scenario Outline: Update from Scalr UI windows test
      Given I have manualy installed scalarizr <default_agent> on M1
      And scalarizr version is valid in M1
      When I change branch for role
      Then I trigger scalarizr update by Scalr UI on M1
      And update process is finished on M1 with status completed
      And scalarizr version is valid in M1
      And scalarizr version is last in M1
      When I execute script 'Windows ping-pong. CMD' synchronous on M1
      Then I see script result in M1
      And script output contains 'pong' in M1

    Examples:
      | default_agent |
      | 3.8.5         |
      | 3.12.7        |

    @manual @ec2 @gce
    Scenario Outline: Update from Scalr UI windows test
      Given I have manualy installed scalarizr <default_agent> on M2
      And scalarizr version is valid in M2
      When I install new scalarizr to the server M2
      Then update process is finished on M2 with status completed
      And scalarizr version is valid in M2
      And scalarizr version is last in M2
      When I execute script 'Windows ping-pong. CMD' synchronous on M2
      Then I see script result in M2
      And script output contains 'pong' in M2

    Examples:
      | default_agent |
      | 3.8.5         |
      | 3.12.7        |
