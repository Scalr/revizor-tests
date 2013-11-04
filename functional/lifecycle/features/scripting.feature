Feature: Scalarizr scripting test

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstrapping role
        Given I have a clean and stopped farm
        When I add role to this farm with scripts
        When I start farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify script execution on bootstrapping
        Then <message> event in script log for M1 from user <user> and exitcode <exitcode>

    Examples:
      | message      | state         | user    | exitcode |
      | HostInit     | bootstrapping | root    | 0        |
      | BeforeHostUp | initializing  | revizor | 1        |
      | HostUp       | running       | ubuntu  | 0        |

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