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
      | HostInit     | https://gist.githubusercontent.com | root     | 0        | Script runned from URL |
      | BeforeHostUp | Linux ping-pong               | root     | 0        | pong   |
      | BeforeHostUp | chef                          | root     | 0        | "HOME"=>"/root"; "USER"=>"root" |
      | HostUp       | Linux ping-pong               | revizor2 | 1        |        |
      | HostUp       | /home/revizor/local_script.sh | revizor  | 0        | Local script work! User: revizor; USER=revizor; HOME=/home/revizor |
      | HostUp       | Linux ping-pong               | revizor  | 0        | pong   |
      | HostUp       | chef                          | root     | 0        |        |
      | HostUp       | /bin/uname                    | root     | 0        | Linux  |

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify chef executed normally
        Given file '/root/chef_solo_result' exist in M1
        Given file '/root/chef_hostup_result' exist in M1
        And process 'memcached' has options '-m 1024' in M1
        And M1 chef runlist has only recipes [memcached,revizorenv]

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario Outline: Scripts executing on linux
        When I execute <script_type> '<script_name>' <execute_type> on M1
        And I see script result in M1
        And script result contains '<output>' on M1

    Examples:
      | script_name                    | execute_type | script_type | output                                    |
      | Restart scalarizr              | synchronous  | remote      | None                                      |
      | Linux ping-pong                | asynchronous | remote      | pong                                      |
      | Linux ping-pong                | synchronous  | remote      | pong                                      |
      | /home/revizor/local_script.sh  | synchronous  | local       | Local script work!\nUSER=root\nHOME=/root |
      | /home/revizor/local_script.sh  | asynchronous | local       | Local script work!\nUSER=root\nHOME=/root |

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstrapping role with failed script
        When I stop farm
        And wait all servers are terminated
        Given I have a clean and stopped farm
        When I add role to this farm with failed_script
        When I start farm
        Then I wait server M2 in failed state