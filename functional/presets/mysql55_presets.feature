Using step definitions from: steps/common_steps
Feature: Mysql55 preset test

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstraping mysql2 role
        Given I have a an empty running farm
        When I add mysql2 role to this farm
        Then I expect server bootstrapping as M1
        And mysql2 is running on M1
        And scalarizr version is last in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify preset screen work and save default config
        Given "my.cnf" file from mysql2 presets config
        And "my.cnf" file from mysql2 contains keys [mysqld/sync_binlog,mysqld/innodb_flush_log_at_trx_commit]
        And I save "my.cnf" content for mysql2 presets

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify scalarizr save normal configuration
        Given "my.cnf" file from mysql2 presets config
        Then I change keys in "my.cnf" file from mysql2 to {mysqld/max_binlog_size:150M,mysqld/max_allowed_packet:24M}
        When I save "my.cnf" content for mysql2 presets
        Given "my.cnf" file from mysql2 presets config
        And "my.cnf" file from mysql2 contains values {mysqld/max_binlog_size:150M,mysqld/max_allowed_packet:24M}
        And not ERROR in M1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify scalarizr save new field
        Given "my.cnf" file from mysql2 presets config
        Then I add keys in "my.cnf" file from mysql2 to {mysqld/slow_launch_time:2}
        When I save "my.cnf" content for mysql2 presets
        Given "my.cnf" file from mysql2 presets config
        And "my.cnf" file from mysql2 contains values {mysqld/slow_launch_time:2}
        And not ERROR in M1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify scalarizr revert bad key
        Given "my.cnf" file from mysql2 presets config
        Then I add keys in "my.cnf" file from mysql2 to {mysqld/testbad_field:doown}
        When I save "my.cnf" content for mysql2 presets I get error with "mysqld/testbad_field"
        Given "my.cnf" file from mysql2 presets config
        And "my.cnf" file from mysql2 not contains keys [mysqld/testbad_field]
        And not ERROR in M1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify scalarizr revert bad value
        Given "my.cnf" file from mysql2 presets config
        Then I add keys in "my.cnf" file from mysql2 to {mysqld/max_binlog_size:twelve,mysqld/max_allowed_packet:24M}
        When I save "my.cnf" content for mysql2 presets I get error
        Given "my.cnf" file from mysql2 presets config
        And "my.cnf" file from mysql2 contains values {mysqld/max_binlog_size:150M,mysqld/max_allowed_packet:24M}
        And not ERROR in M1 scalarizr log