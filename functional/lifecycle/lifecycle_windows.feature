Using step definitions from: steps/common_steps, steps/windows_steps, steps/lifecycle_steps, steps/scripting_steps, steps/szradm_steps, steps/chef_boot_steps
Feature: Windows server lifecycle
    In order to manage server lifecycle
    As a scalr user
    I want to be able to monitor server state changes

    @ec2 @gce @openstack @azure
    Scenario: Bootstraping
        Given I have a clean and stopped farm
        And I add role to this farm with storages
        When I start farm
        Then I see pending server M1
        And I wait and see running server M1
        And instance vcpus info not empty for M1
        And server M1 has disks E:\(test_label) 1 Gb, D:\ 2 Gb, C:\diskmount\ 3 Gb
        And scalarizr version is last in M1
        And hostname in M1 is valid

    @ec2 @gce @openstack @azure @szradm
    Scenario: Verify szradm list-roles
        When I run "szradm -q list-roles" on M1
        And output contain M1 external ip
        When I run "szradm --queryenv get-latest-version" on M1
        And the key "version" has 1 record on M1
        When I run "szradm list-messages" on M1
        And the key "name" has record "HostUp" on M1

    @ec2 @gce @openstack @azure
    Scenario: Restart scalarizr
        Given I have running server M1
        When I reboot windows scalarizr in M1
        And see 'Scalarizr terminated' in M1 windows log
        And scalarizr is running on M1
        And not ERROR in M1 scalarizr windows log

#    @ec2 @gce @openstack
#    Scenario: Restart scalarizr by script
#      Given I have running server M1
#      When I execute script 'windows restart scalarizr' synchronous on M1
#      And see 'Scalarizr terminated' in M1 windows log
#      And scalarizr is running on M1
#      And not ERROR in M1 scalarizr windows log
#      And I see script result in M1
#      And script output contains 'Stopping Scalarizr; Stopped!; Starting Scalarizr; Started!' in M1

    @ec2 @gce @openstack @azure
    Scenario: Restart scalarizr during script execution
      Given I have running server M1
      When I execute script 'windows sleep 60' synchronous on M1
      When I reboot windows scalarizr in M1
      And see 'Scalarizr terminated' in M1 windows log
      And scalarizr is running on M1
      And not ERROR in M1 scalarizr windows log
      And I see script result in M1

    @ec2 @gce @openstack @azure
    Scenario: Windows reboot
        When I reboot server M1
        Then Scalr receives Win_HostDown from M1
        And Scalr receives RebootFinish from M1
        And Scalr sends RebootFinish to M1
        And scalarizr is running on M1
        And scalr-upd-client is running on M1

    @ec2 @gce @openstack @azure
    Scenario Outline: Scripts executing on Windows
        Given I have running server M1
        When I execute '<script_type>' '<script_name>' '<execute_type>' on M1
        And I see script result in M1
        And script output contains '<output>' in M1
        And script stderr output contains '<stderr>' in M1

    Examples:
        | script_name            | execute_type | script_type  | output | stderr |
        | Windows ping-pong. CMD | synchronous  |              | pong   | |
        | Windows ping-pong. CMD | asynchronous |              | pong   | |
        | Windows ping-pong. PS  | synchronous  |              | pong   | |
        | Windows ping-pong. PS  | asynchronous |              | pong   | |
        | Cross-platform script  | asynchronous |              | Multiplatform script successfully executed | |
        | https://gist.githubusercontent.com/gigimon/d233b77be7c04480c01a/raw/cd05c859209e1ff23961a371e0e2298ab3fb0257/gistfile1.txt| asynchronous | local | Script runned from URL | |
        | https://gist.githubusercontent.com/Theramas/48753f91f4af72be12c03c0485b27f7d/raw/97caf55e74c8db6c5bf96b6a29e48c043ac873ed/test| asynchronous | local | Multiplatform script successfully executed | |
        | Non ascii script wrong interpreter | asynchronous | | | The only supported interpreters on Windows in first shebang are ('powershell', 'cmd') |

    @ec2 @gce @openstack @azure
    Scenario: Restart farm
        When I stop farm
        And wait all servers are terminated
        Then I start farm
        And I expect server bootstrapping as M1
        And hostname in M1 is valid

    @ec2 @gce @openstack @azure
    Scenario: Reboot on bootstrapping
        Given I have a clean and stopped farm
        And I add role to this farm with small_win_orchestration
        When I start farm
        And I see pending server M1
        When I wait server M1 in initializing state
        Then I wait server M1 in running state
        And hostname in M1 is valid

    @ec2 @gce @openstack @azure
    Scenario Outline: Verify script execution on bootstrapping
        Then script <name> executed in <event> with exitcode <exitcode> and contain <stdout> for M1

        Examples:
            | event        | name                          | exitcode | stdout |
            | HostInit     | Windows_ping_pong_CMD         | 0        | pong   |
            | HostUp       | Windows_ping_pong_CMD         | 0        | pong   |


    @ec2 @gce @openstack @azure
    Scenario: Bootstrapping role with failed script
        Given I have a clean and stopped farm
        When I add role to this farm with failed_script
        When I start farm
        Then I wait server M2 in failed state
        And Initialization was failed on "BeforeHostUp" phase with "execute.script\bin\Multiplatform_exit_1.ps1 exited with code 1" message on M2

    @ec2
    Scenario: Bootstraping with ephemeral
        Given I have a clean and stopped farm
        And I add role to this farm with ephemeral
        When I start farm
        Then I see pending server M1
        And I wait and see running server M1
        And instance vcpus info not empty for M1
        And server M1 has disks Z:\(test_label) 4 Gb
        And scalarizr version is last in M1
