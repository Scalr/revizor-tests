Using step definitions from: steps/common_steps, steps/lifecycle_steps, steps/docker_steps
Feature: Docker compatibility

    @ec2 @gce
    Scenario: Bootstraping
        Given I have a clean and stopped farm
        And I add role to this farm
        When I start farm
        And I expect server bootstrapping as M1
        Then I install docker on M1
        And I start docker containers on M1
        Then verify containers on Scalr and M1 are identical

    Scenario: Delete docker containers
        Given I have running server M1
        When I delete 10 of the running containers on M1
        Then verify containers on Scalr and M1 are identical

    Scenario: Stop/resume docker containers
        Given I have running server M1
        When I stop 10 of the running containers on M1
        Then verify containers on Scalr and M1 are identical
        When I start stopped containers on M1
        Then verify containers on Scalr and M1 are identical
