Using step definitions from: steps/common_steps, steps/windows_steps, steps/lifecycle_steps, steps/scripting_steps, steps/szradm_steps, steps/provision_linux_steps
Feature: Windows server provision with chef and ansible tower
    In order to manage server lifecycle
    As a scalr user
    I want to be able to monitor server state changes

    @ec2 @gce @openstack @azure
    Scenario: Bootstrapping with chef
        Given I have a clean and stopped farm
        When I add role to this farm with winchef
        When I start farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
        And server M1 exists on chef nodes list
        And M1 chef runlist has only recipes [windows_file_create,revizorenv,revizor_chef_multi]
        And file 'C:\chef_result_file' exist in M1 windows
        And file 'C:\changed_result' exist in M1 windows
        And chef node_name in M1 set by global hostname
        And chef log in M1 contains "revizor_chef_variable=REVIZOR_CHEF_VARIABLE_VALUE_WORK"

    @ec2 @gce @openstack @azure
    Scenario: Verify Scalr delete chef-fixtures
        When I stop farm
        And wait all servers are terminated
        And server M1 not exists on chef nodes list

    @ec2 @gce @openstack @azure
    Scenario: Bootstrapping role with chef-solo
        Given I have a clean and stopped farm
        When I add role to this farm with <settings>
        When I start farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
        And file 'C:\<settings>' exist in M1 windows
        And last script data is deleted on M1

    Examples:
      | settings                |
      | chef-solo-private       |
      | chef-solo-public        |
      | chef-solo-public-branch |

    @ec2 @gce @openstack @azure
    Scenario: Chef bootstrap failure
        Given I have a clean and stopped farm
        When I add role to this farm with chef-fail
        When I start farm
        Then I see failed server M1
        And Initialization was failed on "HostInit" phase with "C:\opscode\chef\bin\chef-client exited with code 1" message on M1
        And chef log in M1 contains "NoMethodError: undefined method `fatal!'"
        And chef bootstrap failed in M1

    @ec2 @gce @openstack @azure
    Scenario: Bootstraping from chef-role
        Given I have a clean and stopped farm
        And I add role to this farm with winchef-role
        When I start farm
        Then I see pending server M1
        And I wait and see running server M1
        And file 'C:\chef_result_file' exist in M1 windows
        And scalarizr version is last in M1
        And hostname in M1 is valid

    @ec2 @gce @openstack @azure
    Scenario: Setup Ansible Tower Bootstrap Configurations
        Given I get Ansible Tower server id
        And I create a New AT 'regular' group 'G1' for Inventory 'Revizor_windows_33'
        And AT group 'G1' exists in inventory 'Revizor_windows_33' in AT server
        And I add a new link with os 'windows' and Inventory 'Revizor_windows_33' and create credentials 'Revizor-windows-cred'
        And credential 'Revizor-windows-cred' exists in ansible-tower credentials list
        And I get and save AT job template id for 'Revizor_windows_Job_Template'

   @ec2 @gce @openstack @azure
    Scenario: Bootstrapping role with Ansible Tower
        Given I have a clean and stopped farm
        When I add role to this farm with ansible-tower
        When I start farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
        And server M1 exists in ansible-tower hosts list

    @ec2 @gce @openstack @azure
    Scenario: Lounch Ansible Tower Job from AT server
        When I launch job 'Revizor_windows_Job_Template' with credential 'Revizor-windows-cred' and expected result 'successful' in M1
        Then I checked that deployment through AT was performed in M1 and the output is 'dir1'

    @ec2 @vmware @gce @cloudstack @openstack @rackspaceng @azure @systemd @stopresume
    Scenario: Suspend/Resume/Reboot server
        When I suspend server M1
        Then I wait server M1 in suspended state
        When I resume server M1
        Then I wait server M1 in resuming state
        Then I wait server M1 in running state
        Given I wait 2 minutes
        When I reboot server M1
        And Scalr receives RebootFinish from M1
        And not ERROR in M1 scalarizr log

    @ec2 @vmware @gce @cloudstack @openstack @rackspaceng @azure @systemd
    Scenario Outline: Verify AT job execution on event
        Then script <name> executed in <event> with exitcode <exitcode> and contain <stdout> for M1

        Examples:
            | event              | name                          | exitcode | stdout     |
            | HostUp             | Revizor_windows_Job_Template  | 0        |   dir1     |
            | RebootComplete     | Revizor_windows_Job_Template  | 0        |   dir1     |
            | ResumeComplete     | Revizor_windows_Job_Template  | 0        |   dir1     |
