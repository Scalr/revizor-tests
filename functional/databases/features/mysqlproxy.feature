Feature: MySQLproxy tests with MySQL backends

    Scenario: Bootstraping MySQLProxy role
        Given I have a an empty running farm
        When I add mysqlproxy role to this farm
        Then I expect server bootstrapping as P1 in mysqlproxy role
        And scalarizr version is last in P1
        And mysqlproxy is running on P1

    Scenario: Bootstraping MySQL role
        When I add mysql role to this farm
        Then I expect server bootstrapping as M1 in mysql role
        And scalarizr version is last in M1
        And mysql is running on M1
        And M1 is writer in P1

    Scenario: Modifying data
        Given I have small-sized database D1 on M1
        When I write data to P1
        Then data in M1
        And I read data from P1
    
    Scenario: Setup replication
        When I increase minimum servers to 2 for mysql role
        Then I expect server bootstrapping as M2 in mysql role
        And scalarizr version is last in M2
        And M2 is slave of M1
        And M2 is reader in P1

    Scenario: Delete mysqlproxy
        When I terminate server P1
        Then I expect server bootstrapping as P2 in mysqlproxy role
        And M1 is writer in P2
        And M2 is reader in P2
        And I read data from P2
    
    Scenario: Delete slave
        When I terminate server M2 with decrease
        And M2 not in P2 config