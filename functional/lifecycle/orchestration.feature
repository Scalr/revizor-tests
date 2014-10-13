Using step definitions from: steps/common_steps, steps/scripting_steps, steps/lifecycle_steps, steps/chef_boot_steps
Feature: Orchestration features test

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstrapping role
        Given I have a clean and stopped farm
        When I add role to this farm with orchestration,chef
        When I start farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify script execution on bootstrapping
        Then script <name> executed in <event> by user <user> with exitcode <exitcode> and contain <stdout> for M1

    Examples:
      | event        | name                          | user     | exitcode | stdout |
      | HostInit     | Revizor orchestration init    | root     | 0        |        |
      | HostInit     | /tmp/script.sh                | root     | 1        |        |
      | HostInit     | local                         | root     | 0        | Script runned from URL |
      | BeforeHostUp | Linux ping-pong               | root     | 0        | pong   |
      | BeforeHostUp | Linux ping-pong               | revizor  | 0        | pong   |
      | HostUp       | Linux ping-pong               | revizor2 | 1        |        |
      | HostUp       | /home/revizor/local_script.sh | revizor  | 0        | Local script work! User: revizor |
      | HostUp       | chef                          | root     | 0        |        |
      | HostUp       | chef                          | root     | 0        |        |

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify chef executed normally
        Given file '/root/chef_solo_result' exist in M1
        Given file '/root/chef_hostup_result' exist in M1
        And process 'memcached' has options '-m 1024' in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Execute 2 sync scripts
        When I execute script 'Linux ping-pong' synchronous on M1
        And I see script result in M1
        Then I execute script 'Linux ping-pong' synchronous on M1
        And I see script result in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Execute 1 sync and 1 async scripts
        When I execute script 'Linux ping-pong' synchronous on M1
        And I see script result in M1
        Then I execute script 'Linux ping-pong' asynchronous on M1
        And I see script result in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Execute restart scalarizr
        When I execute script 'Restart scalarizr' synchronous on M1
        And I see script result in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Execute local script on Linux
        Given I have running server M1
        When I execute local script '/home/revizor/local_script.sh' synchronous on M1
        And I see script result in M1
        And script output contains 'Local script work!' in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstrapping role with failed script
        Given I have a clean and stopped farm
        When I add role to this farm with failed_script
        When I start farm
        Then I wait server M1 in failed state