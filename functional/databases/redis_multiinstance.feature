Feature: Redis database server with multi instance feature via scalr

	@bootstrap
    Scenario: Bootstraping Redis role
        Given I have a an empty running farm
        When I add redis role to this farm with 2 redis processes
        Then I expect server bootstrapping as M1
        And count of redis instance is 2 in M1
        And redis work in ports: 6379,6380 in M1

	@bootstrap
    Scenario: Setup replication
        When I increase minimum servers to 2 for redis role
        Then I expect server bootstrapping as M2
        And scalarizr version is last in M2
		And redis work in ports: 6379,6380 in M2
		And redis instances in M2 is slave

    Scenario: Check replication
        When I write data to redis on port 6379 in M1
        Then I read data from redis on port 6379 in M2
        When I write data to redis on port 6380 in M1
        Then I read data from redis on port 6380 in M2

    Scenario: Bundling data
    	When I trigger databundle creation
    	Then Scalr sends DbMsr_CreateDataBundle to M1
    	And Scalr receives DbMsr_CreateDataBundleResult from M1
    	And Last databundle date updated to current

	Scenario: Backuping data on Master
		When I trigger backup creation
		Then Scalr sends DbMsr_CreateBackup to M2
		And Scalr receives DbMsr_CreateBackupResult from M2
		And Last backup date updated to current

	Scenario: Restart farm
		When I stop farm and store passwords
		And wait all servers are terminated
		Then I start farm
		And I expect server bootstrapping as M1
		And count of redis instance is 2 in M1
		And redis work in ports: 6379,6380 in M1
		And old passwords work in M1