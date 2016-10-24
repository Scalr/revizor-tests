Using step definitions from: steps/bundling_steps, steps/import_steps, steps/cloudinit_steps
Feature: Cloudinit roles bootstrapping

    @ec2 @gce
    Scenario: Create test roles with cloudinit
        Given I have a server running in cloud
        Then I install Chef on server
        When I initiate the installation cloudinit behaviors on the server
        And I check that cloudinit is installed
        Then I create cloudinit image from deployed server
        And I add cloudinit image to the new roles

    @ec2 @gce
    Scenario: Check roles and rebundle
        Given I have a an empty running farm
        When I add <behavior>-cloudinit role to this farm
        Then I expect server bootstrapping as M1
        And <behavior> is running on M1
        And scalarizr version is last in M1
        # Then I rebundle M1
        # When I add to farm role created by last bundle task
        # Then I expect server bootstrapping as M2
        # And <behavior> is running on M2
        # And scalarizr version is last in M2


    Examples:
      | behavior                      |
      | mysql                         |
      | apache                        |
      | redis                         |
      | haproxy                       |
      | postgresql                    |
      | rabbitmq                      |
