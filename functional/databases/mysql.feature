Using step definitions from: steps/common_steps
Feature: MySQL (old behavior) database server

    @ec2 @gce @cloudstack @rackspaceng @openstack @boot
    Scenario: Bootstraping MySQL role
        Given I have a an empty running farm
        When I add mysql role to this farm
        Then I expect server bootstrapping as M1
        And mysql is running on M1
        And scalarizr version is last in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack @restart
    Scenario: Restart scalarizr
       When I reboot scalarizr in M1
       And see 'Scalarizr terminated' in M1 log
       And not ERROR in M1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack @rebundle
    Scenario: Rebundle server
        When I create server snapshot for M1
        Then Bundle task created for M1
        And Bundle task becomes completed for M1

    @ec2 @gce @cloudstack @rackspaceng @openstack @rebundle
    Scenario: Use new role
        Given I have a an empty running farm
        When I add to farm role created by last bundle task
        Then I expect server bootstrapping as M1

    @ec2 @gce @cloudstack @rackspaceng @openstack @rebundle @restart
    Scenario: Restart scalarizr after bundling
       When I reboot scalarizr in M1
       And see 'Scalarizr terminated' in M1 log
       And not ERROR in M1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack @databundle
    Scenario: Bundling data
        When I trigger databundle creation
        Then Scalr sends Mysql_CreateDataBundle to M1
        And Scalr receives Mysql_CreateDataBundleResult from M1
        And Last databundle date updated to current

    @ec2 @gce @cloudstack @rackspaceng @openstack @oneserv
    Scenario: Modifying data
        Given I have small-sized database D1 on M1
        When I trigger databundle creation
        Then Scalr sends Mysql_CreateDataBundle to M1
        And Scalr receives Mysql_CreateDataBundleResult from M1
        And I terminate server M1
        Then I expect server bootstrapping as M1
        And M1 contains database D1

    @ec2 @gce @cloudstack @rackspaceng @openstack @databundle
    Scenario: Bundling data second time
        When I trigger databundle creation
        Then Scalr sends Mysql_CreateDataBundle to M1
        And Scalr receives Mysql_CreateDataBundleResult from M1
        And Last databundle date updated to current

    @ec2 @cloudstack @rackspaceng @openstack @reboot
    Scenario: Reboot server
        When I reboot server M1
        And Scalr receives RebootFinish from M1

    @ec2 @gce @rackspaceng @openstack @backup
    Scenario: Backuping 11 databases
        When I create 11 databases on M1
        Then I trigger backup creation
        Then Scalr sends Mysql_CreateBackup to M1
        And Scalr receives Mysql_CreateBackupResult from M1
        And Last backup date updated to current
        And not ERROR in M1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack @replication
    Scenario: Setup replication
        When I increase minimum servers to 2 for mysql role
        Then I expect server bootstrapping as M2
        And M2 is slave of M1
        And scalarizr version is last in M2

    @ec2 @gce @cloudstack @rackspaceng @openstack @restart
    Scenario: Restart scalarizr in slave
        When I reboot scalarizr in M2
        And see 'Scalarizr terminated' in M2 log
        And not ERROR in M2 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack @slavetermination
    Scenario: Slave force termination
        When I force terminate M2
        Then Scalr sends HostDown to M1
        And not ERROR in M1 scalarizr log
        And mysql is running on M1
        Then I expect server bootstrapping as M2
        And not ERROR in M1 scalarizr log
        And not ERROR in M2 scalarizr log
        And mysql is running on M1

    @ec2 @cloudstack @volumes
    Scenario: Slave delete volumes
        When I know M2 storages
        And M2 storage is use
        Then I terminate server M2 with decrease
        And M2 storage is deleted
        And not ERROR in M1 scalarizr log

    @ec2 @cloudstack @volumes
    Scenario: Setup replication for volume delete test
        When I increase minimum servers to 2 for mysql role
        Then I expect server bootstrapping as M2
        And M2 is slave of M1

    @ec2 @gce @cloudstack @rackspaceng @openstack @replication
    Scenario: Writing on Master, reading on Slave
        When I create database D2 on M1
        Then M2 contains database D2

    @ec2 @gce @cloudstack @rackspaceng @openstack @promotion
    Scenario: Slave -> Master promotion
        Given I increase minimum servers to 3 for mysql role
        And I expect server bootstrapping as M3
        And M3 contains database D2
        When I create database D3 on M1
        And I terminate server M1 with decrease
        Then Scalr sends Mysql_PromoteToMaster to N1
        And Scalr receives Mysql_PromoteToMasterResult from N1
        And N1 Mysql_PromoteToMasterResult message does not contain errors
        And Scalr sends Mysql_NewMasterUp to all
        And M2 contains database D3

    @ec2 @gce @cloudstack @rackspaceng @openstack @promotion
    Scenario: Check new master replication
        Given I wait 1 minutes
        When I create database D4 on N1
        Then all contains database D4

    @ec2 @gce @cloudstack @rackspaceng @openstack @restartfarm
    Scenario: Restart farm
        When I stop farm
        And wait all servers are terminated
        Then I start farm with delay
        And I expect server bootstrapping as M1
        And mysql is running on M1
        And M1 contains database D3
        And scalarizr version is last in M1
        Then I expect server bootstrapping as M2
        And M2 is slave of M1
        And M2 contains database D3
        And M2 contains database D4