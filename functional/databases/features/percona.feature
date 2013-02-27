Feature: Percona database server

    Scenario: Bootstraping percona role
        Given I have a an empty running farm
        When I add percona role to this farm
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1
        And percona is running on M1

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
        Then Scalr sends Mysql_CreateDataBundle to M1
        And Scalr receives Mysql_CreateDataBundleResult from M1
        And Last databundle date updated to current

    Scenario: Modifying data
        Given I have small-sized database D1 on M1
        When I create a databundle
        And I terminate server M1
        Then I expect server bootstrapping as M1
        And M1 contains database D1

    Scenario: Reboot server
        When I reboot server M1
        Then Scalr receives RebootStart from M1
        And Scalr receives RebootFinish from M1

    @ec2
    Scenario: Backuping data on Master
        When I trigger backup creation
        Then Scalr sends Mysql_CreateBackup to M1
        And Scalr receives Mysql_CreateBackupResult from M1
        And Last backup date updated to current

    Scenario: Setup replication
        When I increase minimum servers to 2 for percona role
        Then I expect server bootstrapping as M2
        And scalarizr version is last in M2
        And M2 is slave of M1

    Scenario: Restart scalarizr in slave
       When I reboot scalarizr in M2
       And see 'Scalarizr terminated' in M2 log
       Then scalarizr process is 2 in M2
       And not ERROR in M2 scalarizr log

	Scenario: Slave force termination
		When I force terminate M2
		Then Scalr sends HostDown to M1
		And not ERROR in M1 scalarizr log
		And percona is running on M1
		And scalarizr process is 2 in M1
		Then I expect server bootstrapping as M2
		And not ERROR in M1 scalarizr log
		And not ERROR in M2 scalarizr log
		And percona is running on M1

	@ec2
	Scenario: Slave delete EBS
		When I know M2 storages
		And M2 storage is use
		Then I terminate server M2 with decrease
		And M2 storage is deleted
		And not ERROR in M1 scalarizr log

	@ec2
	Scenario: Setup replication for EBS test
        When I increase minimum servers to 2 for percona role
        Then I expect server bootstrapping as M2
        And M2 is slave of M1

    Scenario: Writing on Master, reading on Slave
        When I create database D2 on M1
        Then M2 contains database D2

    Scenario: Slave -> Master promotion
        Given I increase minimum servers to 3 for percona role
        And I expect server bootstrapping as M3
        When I create database D3 on M1
        And I terminate server M1 with decrease
        Then Scalr sends Mysql_PromoteToMaster to N1
        And Scalr receives Mysql_PromoteToMasterResult from N1
        And Scalr sends Mysql_NewMasterUp to all
        And M2 contains database D3

	Scenario: Check new master replication
		Given I wait 1 minutes
		When I create database D4 on N1
		Then all contains database D4

	@restart_farm
	Scenario: Restart farm
		When I stop farm
		And wait all servers are terminated
		Then I start farm
		And I expect server bootstrapping as M1
		And scalarizr version is last in M1
		And percona is running on M1
		And M1 contains database D3
		Then I expect server bootstrapping as M2
		And M2 is slave of M1
		And M2 contains database D3