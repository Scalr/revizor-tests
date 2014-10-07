Using step definitions from: steps/common_steps
Feature: MySQL database server with behavior mysql2

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @boot
    Scenario: Bootstraping MySQL role
        Given I have a an empty running farm
        When I add mysql2 role to this farm
        Then I expect server bootstrapping as M1
        And mysql is running on M1
        And scalarizr version is last in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @pmalaunch
    Scenario: Launch phpMyAdmin
        When I trigger pmaaccess creation
        Then I launch pma session
        And pma is available, I see the phpMyAdmin in the title

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @restart
    Scenario: Restart scalarizr
       When I reboot scalarizr in M1
       And see 'Scalarizr terminated' in M1 log
       And not ERROR in M1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @rebundle
    Scenario: Rebundle server
        When I create server snapshot for M1
        Then Bundle task created for M1
        And Bundle task becomes completed for M1

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @rebundle
    Scenario: Use new role
        Given I have a an empty running farm
        When I add to farm role created by last bundle task as mysql2 role
        Then I expect server bootstrapping as M1

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @rebundle @restart
    Scenario: Restart scalarizr after bundling
       When I reboot scalarizr in M1
       And see 'Scalarizr terminated' in M1 log
       And scalarizr is running on M1
       And not ERROR in M1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @databundle
    Scenario: Bundling data
        When I trigger databundle creation
        And Scalr receives DbMsr_CreateDataBundleResult from M1
        And Last databundle date updated to current

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @oneserv
    Scenario: Modifying data
        When I create new database user 'revizor' on M1
        And I add small-sized database D1 on M1 by user 'revizor'
        When I trigger databundle creation
        And Scalr receives DbMsr_CreateDataBundleResult from M1
        And I terminate server M1
        Then I expect server bootstrapping as M1
        And M1 contains database D1 by user 'revizor'

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @databundle
    Scenario: Bundling data second time
        When I trigger databundle creation
        And Scalr receives DbMsr_CreateDataBundleResult from M1
        And Last databundle date updated to current

    @ec2 @cloudstack @rackspaceng @eucalyptus @reboot
    Scenario: Reboot server
        When I reboot server M1
        And Scalr receives RebootFinish from M1

    @ec2 @gce @rackspaceng @openstack @eucalyptus @backup
    Scenario: Backuping 11 databases
        When I create 11 databases on M1 by user 'revizor'
        Then I trigger backup creation
        And Scalr receives DbMsr_CreateBackupResult from M1
        And Last backup date updated to current
        And not ERROR in M1 scalarizr log

    @ec2 @backup @restore
    Scenario: Restore from backup
        Given I know last backup url
        And I know timestamp from D1 in M1
        When I download backup in M1
        And I delete databases D1,MDB1,MDB10 in M1
        Then I restore databases D1,MDB1,MDB10 in M1
        And database D1 in M1 contains 'table1' with 80 lines
        And database D1 in M1 has relevant timestamp
        And M1 contains databases D1,MDB1,MDB10

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @replication
    Scenario: Setup replication
        When I increase minimum servers to 2 for mysql2 role
        Then I expect server bootstrapping as M2
        And M2 is slave of M1
        And mysql2 replication status is up
        And scalarizr version is last in M2

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @restart
    Scenario: Restart scalarizr in slave
       When I reboot scalarizr in M2
       And see 'Scalarizr terminated' in M2 log
       And scalarizr is running on M2
       And not ERROR in M2 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @slavetermination
    Scenario: Slave force termination
        When I force terminate M2
        Then Scalr sends HostDown to M1
        And not ERROR in M1 scalarizr log
        And mysql is running on M1
        Then I expect server bootstrapping as M2
        And not ERROR in M1 scalarizr log
        And not ERROR in M2 scalarizr log
        And mysql is running on M1

    @ec2 @grow
    Scenario: Grow storage
        When I increase storage to 5 Gb in mysql2 role
        Then grow status is completed
        And new storage size is 5 Gb in mysql2 role
        And not ERROR in M1 scalarizr log
        And not ERROR in M2 scalarizr log

    @ec2 @cloudstack @volumes
    Scenario: Slave delete volumes
        When I know M2 storages
        And M2 storage is use
        Then I terminate server M2 with decrease
        And M2 storage is deleted
        And not ERROR in M1 scalarizr log

    @ec2 @cloudstack @volumes
    Scenario: Setup replication for volume delete test
        When I increase minimum servers to 2 for mysql2 role
        Then I expect server bootstrapping as M2
        And M2 is slave of M1

    @ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @replication
    Scenario: Writing on Master, reading on Slave
        When I create database D2 on M1 by user 'revizor'
        Then M2 contains database D2 by user 'revizor'

	@ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @databundle @slavedatabundle
	Scenario: Check databundle in slave
		When I trigger databundle creation on slave
		And Scalr receives DbMsr_CreateDataBundleResult from M2
        And Last databundle date updated to current

	@ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @promotion
    Scenario: Slave -> Master promotion
        Given I increase minimum servers to 3 for mysql2 role
        And I expect server bootstrapping as M3
        And M3 contains database D2 by user 'revizor'
        When I create database D3 on M1 by user 'revizor'
        And mysql2 replication status is up
        Then I get mysql2 master storage id
        And I terminate server M1 with decrease
        Then Scalr sends DbMsr_PromoteToMaster to N1
        And Scalr receives DbMsr_PromoteToMasterResult from N1
        And Scalr sends DbMsr_NewMasterUp to all
        And I verify mysql2 master storage id
        And mysql2 replication status is up
        And M2 contains database D3 by user 'revizor'

	@ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @promotion
	Scenario: Check new master replication
		Given I wait 1 minutes
		When I create database D4 on N1 by user 'revizor'
		Then all contains database D4 by user 'revizor'

	@ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @databundle @lvm
	Scenario: Bundling data before terminate
        When I trigger databundle creation
        And Scalr receives DbMsr_CreateDataBundleResult from N1
		And Last databundle date updated to current

	@ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @restartfarm
	Scenario: Restart farm
		When I stop farm
		And wait all servers are terminated
        Then I increase storage size to 7 Gb in farm settings for mysql2 role
		Then I start farm with delay
		And I expect server bootstrapping as M1
		And mysql is running on M1
		And M1 contains database D3 by user 'revizor'
		And scalarizr version is last in M1
        And attached volume in M1 has size 7 Gb
		Then I expect server bootstrapping as M2
		And mysql2 replication status is up
		And M2 is slave of M1
		And M2 contains databases D3,D4 by user 'revizor'

	@ec2 @gce @cloudstack @rackspaceng @openstack @eucalyptus @pmalaunch
    Scenario: Launch phpMyAdmin after farm restart
        When I trigger pmaaccess creation
        Then I launch pma session
        And pma is available, I see the phpMyAdmin in the title

    @ec2
    Scenario: Verify storage recreation
        Given I have a M1 attached volume id as V1
        When I stop farm
        And wait all servers are terminated
        Then I delete volume V1
        Then I start farm with delay
        And I expect server bootstrapping as M1
        Then I expect server bootstrapping as M2
        And attached storage in M1 has size 7 Gb
        And M1 doesn't has any databases
        And mysql2 replication status is up
        And M2 is slave of M1