Using step definitions from: steps/common_steps, steps/windows_steps, steps/lifecycle_steps, steps/scripting_steps, steps/szradm_steps, steps/chef_boot_steps
Feature: Windows server provision with chef
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
        And M1 chef runlist has only recipes [windows_file_create,revizorenv]
        And file 'C:\chef_result_file' exist in M1 windows
        And chef node_name in M1 set by global hostname
        And chef log in M1 contains "revizor_chef_variable=REVIZOR_CHEF_VARIABLE_VALUE_WORK"

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
    Scenario: Bootstrapping with chef-solo from private git repo
        Given I have a clean and stopped farm
        And I add role to this farm with chef-solo-private
        When I start farm
        Then I expect server bootstrapping as M1
        And file 'C:\chef-solo-private' exist in M1 windows
        And last script data is deleted on M1
