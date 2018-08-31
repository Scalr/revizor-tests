Using step definitions from: steps/common_steps, steps/lifecycle_steps, steps/scripting_steps, steps/provision_steps, steps/scripting_steps, steps/szradm_steps
Feature: Linux server fast smoke test

    @ec2 @gce @cloudstack @rackspaceng @openstack @azure @boot
    Scenario: Bootstraping
        Given I have a clean and stopped farm
        And I add role to this farm with storages,noiptables,chef,orchestration
        When I start farm
        Then I see pending server M1
        And I wait and see running server M1
        And scalarizr version from system is last in M1
        And hostname in M1 is valid
        And ports [8008,8010,8012,8013,8014] not in iptables in M1
        And chef log in M1 contains "revizor_chef_variable=REVIZOR_CHEF_VARIABLE_VALUE_WORK"

    @ec2 @gce @cloudstack @rackspaceng @openstack @azure
    Scenario: Verify script execution on bootstrapping
        Then script <name> executed in <event> by user <user> with exitcode <exitcode> and contain <stdout> for M1

    Examples:
    | event        | name                          | user     | exitcode | stdout |
    | HostInit     | Revizor orchestration init    | root     | 0        |        |
    | HostInit     | /tmp/script.sh                | root     | 1        |        |
    | HostInit     | local                         | root     | 0        | Script runned from URL |
    | BeforeHostUp | Linux ping-pong               | root     | 0        | pong   |
    | BeforeHostUp | chef                          | root     | 0        | "HOME"=>"/root"; "USER"=>"root" |
    | HostUp       | Linux ping-pong               | revizor2 | 1        |        |
    | HostUp       | /home/revizor/local_script.sh | revizor  | 0        | Local script work! User: revizor; USER=revizor; HOME=/home/revizor |
    | HostUp       | Linux ping-pong               | revizor  | 0        | pong   |
    | HostUp       | chef                          | root     | 0        |        |

    @ec2 @gce @cloudstack @rackspaceng @openstack @azure
    Scenario: Verify chef executed normally
        Given file '/root/chef_solo_result' exist in M1
        Given file '/root/chef_hostup_result' exist in M1
        And process 'memcached' has options '-m 1024' in M1
        And M1 chef runlist has only recipes [memcached,revizorenv]

    @ec2 @gce @cloudstack @rackspaceng @openstack @azure @szradm
    Scenario: Verify szradm list-roles
        When I run "szradm -q list-roles" on M1
        And output contain M1 external ip
        When I run "szradm --queryenv get-latest-version" on M1
        And the key "version" has 1 record on M1
        When I run "szradm list-messages" on M1
        And the key "name" has record "HostInitResponse" on M1

    @ec2 @cloudstack @rackspaceng @azure @reboot
    Scenario: Linux reboot
        Given I have running server M1
        When I reboot server M1
        And Scalr receives RebootFinish from M1

    @ec2 @gce @cloudstack @rackspaceng @openstack @azure @scripting
    Scenario: Execute script on Linux
        Given I have running server M1
        When I execute script 'Linux ping-pong' synchronous on M1
        And I see script result in M1
        And script output contains 'pong' in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack @azure @scripting
    Scenario: Execute non-ascii script on Linux
        Given I have running server M1
        When I execute script 'Non ascii script' synchronous on M1
        Then I see script result in M1
        And script output contains 'Non_ascii_script' in M1