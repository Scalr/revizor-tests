Using step definitions from: steps/steps
Feature: Scalr api v.2 tests

    Scenario: ScalrAPI v.2 rate limiting
      Given I have 2 new api secret keys
      When I generate 5 api queries for one minute
      Then limit error was not triggered by scalr
      When I generate more than 5 api queries for one minute
      Then limit error was triggered by scalr
      When I generate 5 api queries for one minute using second secret key
      Then limit error was not triggered by scalr

    Scenario: ScalrAPI v.2 filed queries logging
      Given I have 1 new api secret keys
      When I generate api queries with failed method
      Then The 404 error was triggered by scalr
