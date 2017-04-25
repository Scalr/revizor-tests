Using step definitions from: steps/bundling_steps, steps/import_steps, steps/cloudinit_steps
Feature: Cloudinit roles bootstrapping
#TODO: Add/Check Cloudstack support
    @ec2
    Scenario Outline: Create test roles with cloudinit
        Given I have a server running in cloud
        And I check that cloudinit is installed
        Then I install Chef on server
        When I initiate the installation <behavior_set> behaviors on the server
        Then I create <behavior_set>-cloudinit image from deployed server
        And I add <behavior_set>-cloudinit image to the new roles as non scalarized

    Examples:
      | behavior_set                  |
      | mbeh1                         |
      | mbeh2                         |


    @ec2
    Scenario Outline: Check roles and rebundle
        Given I have a an empty running farm
        When I add <behavior>-cloudinit role to this farm
        Then I expect server bootstrapping as M1
        And <behavior> is running on M1
        And scalarizr version is last in M1
        Then I rebundle M1
        Given I have a an empty running farm
        When I add to farm role created by last bundle task
        Then I expect server bootstrapping as M2
        And <behavior> is running on M2
        And scalarizr version is last in M2
        And not ERROR in M2 scalarizr debug log
        And not ERROR in M2 scalarizr update log

    Examples:
      | behavior                      |
      | app                           |
      | redis                         |
      | haproxy                       |
      | postgresql                    |
      | mysql2                        |
      | percona                       |
      | tomcat                        |
      | memcached                     |
      | www                           |
      # # | rabbitmq                      | FAM-480
