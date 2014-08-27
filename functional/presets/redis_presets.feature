Using step definitions from: steps/common_steps
Feature: Redis preset test

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstraping redis role
        Given I have a an empty running farm
        When I add redis role to this farm
        Then I expect server bootstrapping as M1
        And redis is running on M1
        And scalarizr version is last in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify preset screen work and save default config
        Given "redis.conf" file from redis presets config
        And "redis.conf" file from redis contains keys [databases,loglevel]
        And I save "redis.conf" content for redis presets

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify scalarizr save normal configuration
        Given "redis.conf" file from redis presets config
        Then I change keys in "redis.conf" file from redis to {databases:12,loglevel:notice}
        When I save "redis.conf" content for redis presets
        Given "redis.conf" file from redis presets config
        And "redis.conf" file from redis contains values {databases:12,loglevel:notice}
        And not ERROR in M1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify scalarizr save new field
        Given "redis.conf" file from redis presets config
        Then I add keys in "redis.conf" file from redis to {maxclients:150}
        When I save "redis.conf" content for redis presets
        Given "redis.conf" file from redis presets config
        And "redis.conf" file from redis contains values {maxclients:150}
        And not ERROR in M1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify scalarizr revert bad key
        Given "redis.conf" file from redis presets config
        Then I add keys in "redis.conf" file from redis to {testbadfield:doown}
        When I save "redis.conf" content for redis presets I get error
        Given "redis.conf" file from redis presets config
        And "redis.conf" file from redis not contains keys [testbadfield]
        And not ERROR in M1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify scalarizr revert bad value
        Given "redis.conf" file from redis presets config
        Then I add keys in "redis.conf" file from redis to {databases:wat}
        When I save "redis.conf" content for redis presets I get error
        Given "redis.conf" file from redis presets config
        And "redis.conf" file from redis contains values {databases:12}
        And not ERROR in M1 scalarizr log