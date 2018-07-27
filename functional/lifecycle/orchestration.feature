Using step definitions from: steps/common_steps, steps/scripting_steps, steps/lifecycle_steps, steps/provision_steps
Feature: Orchestration features test

    @ec2 @gce @vmware @cloudstack @rackspaceng @openstack @azure
    Scenario: Bootstrapping role
        Given I have a clean and stopped farm
        When I add role to this farm with orchestration,chef
        When I start farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1

    @ec2 @gce @vmware @cloudstack @rackspaceng @openstack @azure
    Scenario Outline: Verify script execution on bootstrapping
        Then script <name> executed in <event> by user <user> with exitcode <exitcode> and contain <stdout> for M1

        Examples:
            | event        | name                               | user     | exitcode | stdout                                                             |
            | HostInit     | Revizor orchestration init         | root     | 0        |                                                                    |
            | HostInit     | /tmp/script.sh                     | root     | 1        |                                                                    |
            | HostInit     | https://gist.githubusercontent.com | root     | 0        | Script runned from URL                                             |
            | BeforeHostUp | Linux ping-pong                    | root     | 0        | pong                                                               |
            | BeforeHostUp | chef                               | root     | 0        | "HOME"=>"/root"; "USER"=>"root"                                    |
            | HostUp       | Linux ping-pong                    | revizor2 | 1        | STDERR: no such user: 'revizor2'                                   |
            | HostUp       | /home/revizor/local_script.sh      | revizor  | 0        | Local script work! User: revizor; USER=revizor; HOME=/home/revizor |
            | HostUp       | Linux ping-pong                    | revizor  | 0        | pong                                                               |
            | HostUp       | chef                               | root     | 0        |                                                                    |
            | HostUp       | /bin/uname                         | root     | 0        | Linux                                                              |
            | HostUp       | https://gist.githubusercontent.com | root     | 0        | Multiplatform script successfully executed                         |
            | HostUp       | Sleep 10                           | root     | 130      | printing dot each second; .....                                    |

    @ec2 @gce @vmware @cloudstack @rackspaceng @openstack @azure @chef
    Scenario: Verify chef executed normally
        Given file '/root/chef_solo_result' exist in M1
        Given file '/root/chef_hostup_result' exist in M1
        And process 'memcached' has options '-m 1024' in M1
        And M1 chef runlist has only recipes [memcached,revizorenv]

    @ec2 @gce @vmware @cloudstack @rackspaceng @openstack @azure
    Scenario Outline: Scripts executing on linux
        When I execute '<script_type>' '<script_name>' '<execute_type>' on M1
        And I see script result in M1
        And script output contains '<output>' in M1

        Examples:
            | script_name                   | execute_type | script_type | output                                    |
#            | Restart scalarizr             | synchronous  |             |                                           |
            | Linux ping-pong               | asynchronous |             | pong                                      |
            | Linux ping-pong               | synchronous  |             | pong                                      |
            | /home/revizor/local_script.sh | synchronous  | local       | Local script work!; USER=root; HOME=/root |
            | /home/revizor/local_script.sh | asynchronous | local       | Local script work!; USER=root; HOME=/root |
            | https://gist.githubusercontent.com/Theramas/5b2a9788df316606f72883ab1c3770cc/raw/3ae1a3f311d8e43053fbd841e8d0f17daf1d5d66/multiplatform | asynchronous | local | Multiplatform script successfully executed                                             |
            | Cross-platform script          | asynchronous |            | Multiplatform script successfully executed                                             |

    @ec2 @gce @vmware @cloudstack @rackspaceng @openstack @azure
    Scenario: Bootstrapping role with failed script
        Given I have a clean and stopped farm
        When I add role to this farm with failed_script
        When I start farm
        Then I wait server M2 in failed state
        And Initialization was failed on "BeforeHostUp" phase with "execute.script/bin/Multiplatform_exit_1 exited with code 1" message on M2
