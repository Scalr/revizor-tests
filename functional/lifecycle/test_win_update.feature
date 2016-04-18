Feature: test windows

  Scenario: Update from branch to stable
      Given I have a clean image
      And I add image to the new role
      When I have a an empty running farm
      Then I add created role to the farm
      And I see pending server M1
      Then I install scalarizr to the server M1
      And I reboot hard server M1
      When I expect server bootstrapping as M1
      Then scalarizr version was updated in M1
      When I execute script 'Windows ping-pong. CMD' synchronous on M1
      And I see script result in M1
      And script output contains 'pong' in M1
