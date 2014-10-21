Using step definitions from: steps/common_api_steps, steps/system_api_steps
Feature: Base server role, api tests

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstraping base role
        Given I have a an empty running farm
        When I add base role to this farm with scaling
        Then I expect server bootstrapping as B1
        And scalarizr version is last in B1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Change host name by api
        When I run "SystemApi" command "set_hostname" on B1 with arguments:
            | hostname              |
            | revizor-test.scalr.ws |
        Then api result "set_hostname" contain argument "hostname"
        When I run "SystemApi" command "get_hostname" on B1
        Then api result "get_hostname" contain argument "hostname" from command "set_hostname"
        And not ERROR in B1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Get named arguments of system information by api
        When I run "SystemApi" command "uname" on B1
        Then api result "uname" has "nodename" data
        When I run "SystemApi" command "dist" on B1
        Then api result "dist" has "distributor" data
        When I run "SystemApi" command "net_stats" on B1
        Then api result "net_stats" has "lo" data
        When I run "SystemApi" command "cpu_info" on B1
        Then api result "cpu_info" has "model name" data
        When I run "SystemApi" command "cpu_stat" on B1
        Then api result "cpu_stat" has "system" data
        When I run "SystemApi" command "mem_info" on B1
        Then api result "mem_info" has "total_swap" data
        When I run "SystemApi" command "scaling_metrics" on B1
        Then api result "scaling_metrics" has "name" data
        When I run "SystemApi" command "statvfs" on B1 with arguments:
            | mpoints |
            | ["/"]   |
        And api result "statvfs" has "/" data
        And not ERROR in B1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Get system information by api
        When I run "SystemApi" command "pythons" on B1
        Then api result "pythons" has data
        When I run "SystemApi" command "block_devices" on B1
        Then api result "block_devices" has data
        When I run "SystemApi" command "load_average" on B1
        Then api result "load_average" has data
        When I run "SystemApi" command "disk_stats" on B1
        Then api result "disk_stats" has data
        And not ERROR in B1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Get scalarizr logs by api
        When I run "SystemApi" command "get_debug_log" on B1
        Then api result "get_debug_log" has "Starting scalarizr" logging data
        When I run "SystemApi" command "get_update_log" on B1
        Then api result "get_update_log" has "Starting UpdateClient" logging data
        When I run "SystemApi" command "get_log" on B1
        Then api result "get_log" has "Starting scalarizr" logging data
        And not ERROR in B1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Get scripting logs by api
        Given I execute script 'Linux ping-pong' synchronous on B1
        And I see script result in B1
        Then I get script result by "SystemApi" command "get_script_logs" on B1
        And api result "get_script_logs" has "pong" logging data
        And not ERROR in B1 scalarizr log