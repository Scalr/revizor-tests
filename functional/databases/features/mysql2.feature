Feature: MySQL database server with behavior mysql2

	@promote
    Scenario: Bootstraping MySQL role
        Given I have a an empty running farm
        When I add mysql2 role to this farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
        And mysql is running on M1

	@restart
    Scenario: Restart scalarizr
       When I reboot scalarizr in M1
       And see 'Scalarizr terminated' in M1 log
       Then scalarizr process is 2 in M1
       And not ERROR in M1 scalarizr log

	@rebundle
	Scenario: Rebundle server
        When I create server snapshot for M1
    	Then Bundle task created for M1
        And Bundle task becomes completed for M1

	@rebundle
    Scenario: Use new role
        Given I have a an empty running farm
        When I add to farm role created by last bundle task
        Then I expect server bootstrapping as M1

    @rebundle
    Scenario: Restart scalarizr after bundling
       When I reboot scalarizr in M1
       And see 'Scalarizr terminated' in M1 log
       Then scalarizr process is 2 in M1
       And not ERROR in M1 scalarizr log

    Scenario: Bundling data
        When I trigger databundle creation
        Then Scalr sends DbMsr_CreateDataBundle to M1
        And Scalr receives DbMsr_CreateDataBundleResult from M1
        And Last databundle date updated to current

	@modify
    Scenario: Modifying data
        Given I have small-sized database D1 on M1
        When I create a databundle
        And I terminate server M1
        Then I expect server bootstrapping as M1
        And M1 contains database D1

	@lvm
	Scenario: Bundling data second time
        When I trigger databundle creation
        Then Scalr sends DbMsr_CreateDataBundle to M1
        And Scalr receives DbMsr_CreateDataBundleResult from M1
		And Last databundle date updated to current

	@reboot
    Scenario: Reboot server
        When I reboot server M1
        Then Scalr receives RebootStart from M1
        And Scalr receives RebootFinish from M1

	@backup
    Scenario: Backuping data on Master
        When I trigger backup creation
        Then Scalr sends DbMsr_CreateBackup to M1
        And Scalr receives DbMsr_CreateBackupResult from M1
        And Last backup date updated to current

	@backup
	Scenario: Backuping 11 databases
		When I create 11 databases on M1
		Then I trigger backup creation
		Then Scalr sends DbMsr_CreateBackup to M1
        And Scalr receives DbMsr_CreateBackupResult from M1
		And Last backup date updated to current
		And not ERROR in M1 scalarizr log

	@promote
    Scenario: Setup replication
        When I increase minimum servers to 2 for mysql2 role
        Then I expect server bootstrapping as M2
        And scalarizr version is last in M2
        And M2 is slave of M1

	@restart
    Scenario: Restart scalarizr in slave
       When I reboot scalarizr in M2
       And see 'Scalarizr terminated' in M2 log
       Then scalarizr process is 2 in M2
       And not ERROR in M2 scalarizr log

	Scenario: Slave force termination
		When I force terminate M2
		Then Scalr sends HostDown to M1
		And not ERROR in M1 scalarizr log
		And mysql is running on M1
		And scalarizr process is 2 in M1
		Then I expect server bootstrapping as M2
		And not ERROR in M1 scalarizr log
		And not ERROR in M2 scalarizr log
		And mysql is running on M1

	@grow
	Scenario: Grow storage
		When I increase storage to 5 Gb in mysql2 role
		Then grow status is ok
		And new storage size is 5 Gb in mysql2 role
		And not ERROR in M1 scalarizr log
        And not ERROR in M2 scalarizr log

	@ebs
    Scenario: Slave delete EBS
    	When I know M2 storages
    	And M2 storage is use
    	Then I terminate server M2 with decrease
   		And M2 storage is deleted
   		And not ERROR in M1 scalarizr log

	@ebs
	Scenario: Setup replication for EBS test
        When I increase minimum servers to 2 for mysql2 role
        Then I expect server bootstrapping as M2
        And M2 is slave of M1

	@promote
    Scenario: Writing on Master, reading on Slave
        When I create database D2 on M1
        Then M2 contains database D2

	@promote @slave
	Scenario: Check databundle in slave
		When I trigger databundle creation on slave
		Then Scalr sends DbMsr_CreateDataBundle to M2
		And Scalr receives DbMsr_CreateDataBundleResult from M2
        And Last databundle date updated to current

	@promote
    Scenario: Slave -> Master promotion
        Given I increase minimum servers to 3 for mysql2 role
        And I expect server bootstrapping as M3
        And M3 contains database D2
        When I create database D3 on M1
        And I terminate server M1 with decrease
        Then Scalr sends DbMsr_PromoteToMaster to N1
        And Scalr receives DbMsr_PromoteToMasterResult from N1
        And Scalr sends DbMsr_NewMasterUp to all
        And M2 contains database D3

	@promote
	Scenario: Check new master replication
		Given I wait 1 minutes
		When I create database D4 on N1
		Then all contains database D4

	@lvm
	Scenario: Bundling data before terminate
        When I trigger databundle creation
        Then Scalr sends DbMsr_CreateDataBundle to M1
        And Scalr receives DbMsr_CreateDataBundleResult from M1
		And Last databundle date updated to current

	@restart_farm
	Scenario: Restart farm
		When I stop farm
		And wait all servers are terminated
		Then I start farm
		And I expect server bootstrapping as M1
		And scalarizr version is last in M1
		And mysql is running on M1
		And M1 contains database D3
		Then I expect server bootstrapping as M2
		And M2 is slave of M1
		And M2 contains database D3