Using step definitions from: steps/common_steps
Feature: Postgresql preset test

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstraping postgresql role
        Given I have a an empty running farm
        When I add postgresql role to this farm
        Then I expect server bootstrapping as M1
        And postgresql is running on M1
        And scalarizr version is last in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify preset screen work and save default config
        Given "postgresql.conf" file from postgresql presets config
        And "postgresql.conf" file from postgresql contains keys [max_connections,timezone]
        And I save "postgresql.conf" content for postgresql presets

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify scalarizr save normal configuration
        Given "postgresql.conf" file from postgresql presets config
        Then I change keys in "postgresql.conf" file from postgresql to {max_connections:150}
        When I save "postgresql.conf" content for postgresql presets
        Given "postgresql.conf" file from postgresql presets config
        And "postgresql.conf" file from postgresql contains values {max_connections:150}
        And not ERROR in M1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify scalarizr save new field
        Given "postgresql.conf" file from postgresql presets config
        Then I add keys in "postgresql.conf" file from postgresql to {temp_buffers:10M}
        When I save "postgresql.conf" content for postgresql presets
        Given "postgresql.conf" file from postgresql presets config
        And "postgresql.conf" file from postgresql contains values {temp_buffers:10M}
        And not ERROR in M1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify scalarizr revert bad key
        Given "postgresql.conf" file from postgresql presets config
        Then I add keys in "postgresql.conf" file from postgresql to {testbadfield:doown}
        When I save "postgresql.conf" content for postgresql presets I get error
        Given "postgresql.conf" file from postgresql presets config
        And "postgresql.conf" file from postgresql not contains keys [testbadfield]
        And not ERROR in M1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify scalarizr revert bad value
        Given "postgresql.conf" file from postgresql presets config
        Then I add keys in "postgresql.conf" file from postgresql to {max_connections:150W}
        When I save "postgresql.conf" content for postgresql presets I get error
        Given "postgresql.conf" file from postgresql presets config
        And "postgresql.conf" file from postgresql contains values {max_connections:150W}
        And not ERROR in M1 scalarizr log