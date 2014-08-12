Using step definitions from: steps/common_steps
Feature: Percona55 preset test

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstraping percona role
        Given I have a an empty running farm
        When I add percona role to this farm
        Then I expect server bootstrapping as M1
        And percona is running on M1
        And scalarizr version is last in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify preset screen work
        Given "my.cnf" file from percona presets config
        And "my.cnf" file from percona contains keys [mysqld/binlog_format,mysqld/log-bin-index,mysqld/key_buffer_size]

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Save getted config
        Given "my.cnf" file from percona presets config
        When I save "my.cnf" content for percona presets
        Then I don't get any error

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify scalarizr save normal configuration
        Given "my.cnf" file from percona presets config
        Then I change keys in "my.cnf" file from percona to {mysqld/max_allowed_packet:2M,mysqld/read_buffer_size:512K}
        When I save "my.cnf" content for percona presets
        And I don't get any error
        Given "my.cnf" file from percona presets config
        And "my.cnf" file from percona contains values {mysqld/max_allowed_packet:2M,mysqld/read_buffer_size:512K}

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify scalarizr save new field
        Given "my.cnf" file from percona presets config
        Then I add key {mysqld/slow_launch_time:2} to "my.cnf" file
        When I save "my.cnf" content for percona presets
        Then I don't get any error
        Given "my.cnf" file from percona presets config
        And "my.cnf" file from percona contains values {mysqld/slow_launch_time:2}