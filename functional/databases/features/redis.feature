Feature: Redis database server functional test

	@ec2 @gce @cloudstack @rackspaceng @boot
    Scenario: Bootstraping redis role
        Given I have a an empty running farm
        When I add redis role to this farm
        Then I expect server bootstrapping as M1
        And redis is running on M1
        And scalarizr version is last in M1

	@ec2 @gce @cloudstack @rackspaceng @restart
    Scenario: Restart scalarizr
       When I reboot scalarizr in M1
       And see 'Scalarizr terminated' in M1 log
       Then scalarizr process is 2 in M1
       And not ERROR in M1 scalarizr log

	@ec2 @gce @cloudstack @rackspaceng @rebundle
	Scenario: Rebundle server
        When I create server snapshot for M1
    	Then Bundle task created for M1
        And Bundle task becomes completed for M1

	@ec2 @gce @cloudstack @rackspaceng @rebundle
    Scenario: Use new role
        Given I have a an empty running farm
        When I add to farm role created by last bundle task
        Then I expect server bootstrapping as M1

    @ec2 @gce @cloudstack @rackspaceng @restart
    Scenario: Restart scalarizr after bundling
       When I reboot scalarizr in M1
       And see 'Scalarizr terminated' in M1 log
       Then scalarizr process is 2 in M1
       And not ERROR in M1 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @databundle
    Scenario: Bundling data
        When I trigger databundle creation
        Then Scalr sends DbMsr_CreateDataBundle to M1
        And Scalr receives DbMsr_CreateDataBundleResult from M1
        And Last databundle date updated to current

	@ec2 @gce @cloudstack @rackspaceng @oneserv
    Scenario: Modifying data
        Given I have small-sized database 1 on M1
        When I create a databundle
        And I terminate server M1
        Then I expect server bootstrapping as M1
        And M1 contains database 1

	@ec2 @gce @cloudstack @rackspaceng @databundle
	Scenario: Bundling data second time
        When I trigger databundle creation
        Then Scalr sends DbMsr_CreateDataBundle to M1
        And Scalr receives DbMsr_CreateDataBundleResult from M1
		And Last databundle date updated to current

	@ec2 @cloudstack @rackspaceng @reboot
    Scenario: Reboot server
        When I reboot server M1
        And Scalr receives RebootFinish from M1

	@ec2 @gce @rackspaceng @backup
    Scenario: Backuping data on Master
        When I trigger backup creation
        Then Scalr sends DbMsr_CreateBackup to M1
        And Scalr receives DbMsr_CreateBackupResult from M1
        And Last backup date updated to current

	@ec2 @gce @cloudstack @rackspaceng @replication
    Scenario: Setup replication
        When I increase minimum servers to 2 for redis role
        Then I expect server bootstrapping as M2
        And M2 is slave of M1
        And scalarizr version is last in M2

	@ec2 @gce @cloudstack @rackspaceng @restart
    Scenario: Restart scalarizr in slave
       When I reboot scalarizr in M2
       And see 'Scalarizr terminated' in M2 log
       Then scalarizr process is 2 in M2
       And not ERROR in M2 scalarizr log

    @ec2 @gce @cloudstack @rackspaceng @slavetermination
	Scenario: Slave force termination
		When I force terminate M2
		Then Scalr sends HostDown to M1
		And not ERROR in M1 scalarizr log
		And redis is running on M1
		And scalarizr process is 2 in M1
		Then I expect server bootstrapping as M2
		And not ERROR in M1 scalarizr log
		And not ERROR in M2 scalarizr log
		And redis is running on M1

	@ec2 @cloudstack @volumes
    Scenario: Slave delete volumes
    	When I know M2 storages
    	And M2 storage is use
    	Then I terminate server M2 with decrease
   		And M2 storage is deleted
   		And not ERROR in M1 scalarizr log

	@ec2 @cloudstack @volumes
	Scenario: Setup replication for volume delete test
        When I increase minimum servers to 2 for redis role
        Then I expect server bootstrapping as M2
        And M2 is slave of M1

	@ec2 @gce @cloudstack @rackspaceng @replication
    Scenario: Writing on Master, reading on Slave
        When I create database 2 on M1
        Then M2 contains database 2

	@ec2 @gce @cloudstack @rackspaceng @databundle
	Scenario: Check databundle in slave
		When I trigger databundle creation on slave
		Then Scalr sends DbMsr_CreateDataBundle to M2
		And Scalr receives DbMsr_CreateDataBundleResult from M2
        And Last databundle date updated to current

	@ec2 @gce @cloudstack @rackspaceng @promotion
    Scenario: Slave -> Master promotion
        Given I increase minimum servers to 3 for redis role
        And I expect server bootstrapping as M3
        And M3 contains database 2
        When I create database 3 on M1
        And I terminate server M1 with decrease
        Then Scalr sends DbMsr_PromoteToMaster to N1
        And Scalr receives DbMsr_PromoteToMasterResult from N1
        And Scalr sends DbMsr_NewMasterUp to all
        And M2 contains database 3

	@ec2 @gce @cloudstack @rackspaceng @promotion
	Scenario: Check new master replication
		Given I wait 1 minutes
		When I create database 4 on N1
		Then all contains database 4

	@ec2 @gce @cloudstack @rackspaceng @databundle @lvm
	Scenario: Bundling data before terminate
        When I trigger databundle creation
        Then Scalr sends DbMsr_CreateDataBundle to N1
        And Scalr receives DbMsr_CreateDataBundleResult from N1
		And Last databundle date updated to current

	@ec2 @gce @cloudstack @rackspaceng @restartfarm
	Scenario: Restart farm
		When I stop farm
		And wait all servers are terminated
		Then I start farm with delay
		And I expect server bootstrapping as M1
		And redis is running on M1
		And M1 contains database D3
		And scalarizr version is last in M1
		Then I expect server bootstrapping as M2
		And M2 is slave of M1
		And M2 contains database 3
		And M2 contains database 4