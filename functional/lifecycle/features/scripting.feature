Feature: Scalarizr scripting test

	Scenario: Background
		Given I have a clean and stopped farm
		When I add role to this farm with scripts attached
		When I start farm
		Then I expect server bootstrapping as M1
		And scalarizr version is last in M1

	Scenario: Bootstrapping role
		Then <message> event in script log for M1

	Examples:
	  | message      | state         |
	  | HostInit     | bootstrapping |
	  | BeforeHostUp | initializing  |
	  | HostUp       | running       |

	Scenario: Execute 2 sync scripts
		When I execute script 'Linux ping-pong' synchronous on M1
		And I see script result in M1
		Then I execute script 'Linux ping-pong' synchronous on M1
		And I see script result in M1

	Scenario: Execute 1 sync and 1 async scripts
    	When I execute script 'Linux ping-pong' synchronous on M1
    	And I see script result in M1
    	Then I execute script 'Linux ping-pong' asynchronous on M1
    	And I see script result in M1

	Scenario: Execute restart scalarizr
    	When I execute script 'Restart scalarizr' synchronous on M1
    	And I see script result in M1