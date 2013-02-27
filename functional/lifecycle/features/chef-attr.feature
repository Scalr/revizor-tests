Feature: Check chef attributes set

    Scenario: Bootstrapping
    	Given I have a clean and stopped farm
    	When I add role to this farm with chef settings
    	When I launch the farm
    	Then I expect server bootstrapping as M1
    	And scalarizr version is last in M1
		And process 'memcached' has options '-m 1024' in M1
