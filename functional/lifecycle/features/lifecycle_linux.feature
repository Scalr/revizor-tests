Feature: Linux server lifecycle
    In order to manage server lifecycle
    As a scalr user
    I want to be able to monitor server state changes

    @boot
    Scenario: Bootstraping
        Given I have a clean and stopped farm
        And I add role to this farm with deploy
        When I start farm
        Then I see pending server
        And I wait and see initializing server
        And I wait and see running server
        And scalarizr version is last in server
        Then Scalr receives DeployResult
        And directory '/var/www/src' exist

    @boot @reboot
    Scenario: Linux reboot
        Given I have running linux server
        When I reboot it
        And Scalr receives RebootFinish

    Scenario: Execute script on Linux
        Given I have running linux server
        When I execute on it script 'Linux ping-pong'
        Then I see execution result in scripting log
        And script output contains 'pong'

    Scenario: Execute non-ascii script on Linux
        Given I have running linux server
        When I execute on it script 'Non ascii script'
        Then I see execution result in scripting log
        And script output contains 'Non_ascii_script'

    Scenario: Restart scalarizr
       Given I have running linux server
       When I reboot scalarizr
       And see 'Scalarizr terminated' in log
       Then scalarizr process is 2
       And not ERROR in log

	Scenario: Custom event
		Given I define event 'TestEvent'
		And I attach a script 'TestingEventScript' on this event
		When I execute 'szradm --fire-event TestEvent file1=/tmp/f1 file2=/tmp/f2'
		Then Scalr sends TestEvent
		And server contain '/tmp/f1'
		And server contain '/tmp/f2'

   Scenario: Check deploy action
       Given I have running linux server
       When I deploy app with name 'deploy-test'
       And Scalr sends Deploy
       Then Scalr receives DeployResult
       And deploy task deployed

   @restart_farm
   Scenario: Restart farm
	   When I stop farm
	   And wait all servers are terminated
	   Then I start farm
	   And I expect server bootstrapping as M1