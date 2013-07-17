Feature: Import server to scalr and use this role

    Scenario: Executing import command on mbeh1
        Given I have a mbeh1 server running in cloud
        When I execute on it import command with changed server
        Then scalarizr send Hello message
        And Hello message contain behaviors: chef,app,mysql2,redis,postgresql,rabbitmq


    Scenario: Executing import command on mbeh2
        Given I have a mbeh2 server running in cloud
        When I execute on it import command with changed server
        Then scalarizr send Hello message
        And Hello message contain behaviors: chef,www,mysqlproxy,percona