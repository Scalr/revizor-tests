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
    Scenario: Bootstrapping role with Ansible Tower
        Given I have a clean and stopped farm
        And I add a new link with os 'windows' and Inventory 'Revizor_windows_33' and create credentials 'Revizor_windows_cred'
        And credential 'Revizor_windows_cred' exists in ansible-tower credentials list
        When I add role to this farm with ansible-tower
        When I start farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
        And server M1 exists in ansible-tower hosts list
        And I launch job 'Revizor windows Job Template' with credential 'Revizor_windows_cred' and expected result 'successful' in M1
        And I checked that deployment through AT was performed in M1 and the output is 'dir1'
