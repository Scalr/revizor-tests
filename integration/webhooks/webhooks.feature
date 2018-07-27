Feature: Check fatmouse/workflow_engine webhooks implementation

  Scenario: Prepare test-env
    Given I have configured scalr config:
        | name                                             | value |
        | scalr.system.webhooks.scalr_labs_workflow_engine | true  |
        | scalr.system.webhooks.ssl_verify                 | false |
        | scalr.system.webhooks.retry_interval             | 5     |
        | scalr.system.webhooks.use_proxy                  | false |
    Then I stop service "dbqueue"
    Then I restart service "workflow-engine"
    Then I restart service "zmq_service"
    When I have configured revizor environment:
      | name           | value          |
      | platform       | gce            |
      | dist           | ubuntu1604     |
    And I have a clean and stopped farm
    And I add role to this farm
    When I start farm
    Then I expect server bootstrapping as F1
    When I configure nginx/flask on F1
    And http get F1 contains default welcome message


  Scenario: Check Webhooks with ssl_verify=false
    Given Scalr services zmq_service,workflow-engine are in RUNNING state
    And Scalr services dbqueue are in STOPPED state
    Then I add F1 webhooks to Scalr:
      | schema | endpoint    | trigger_event | name           |
      | http   | /           | AccountEvent  | http_normal    |
      | http   | /redirect   | AccountEvent  | http_redirect  |
      | http   | /abort404   | AccountEvent  | http_404       |
      | http   | /abort500   | AccountEvent  | http_500       |
      | http   | /retry      | AccountEvent  | http_retry     |
      | https  | /redirect   | AccountEvent  | https_redirect |
      | https  | /abort404   | AccountEvent  | https_404      |
      | https  | /abort500   | AccountEvent  | https_500      |
      | https  | /           | AccountEvent  | https_normal   |
    When I execute 'szradm --fire-event AccountEvent' in F1
    And I assert F1 webhook results:
      | webhook_name   | expected_response | attempts | error |
      | http_normal    | 200               | 1        |       |
      | http_redirect  | 200               | 1        |       |
      | http_404       | 404               | 1        |       |
      | http_500       | 500               | 2        |       |
      | http_retry     | 200               | 2        |       |
      | https_redirect | 200               | 1        |       |
      | https_404      | 404               | 1        |       |
      | https_500      | 500               | 2        |       |
      | https_normal   | 200               | 1        |       |
    And no "Traceback" in service "workflow-engine" log


  @scalr_mail_service
  Scenario: Check SCALR_MAIL_SERVICE
    Given I set scalr_mail_service_url in TestEnv config
    And I add SCALR_MAIL_SERVICE webhook
    Then I restart service "workflow-engine"
    When I execute 'szradm --fire-event ScalrEvent' in F1
    Then SCALR_MAIL_SERVICE result is successful
    And no "Traceback" in service "workflow-engine" log


  @proxy
  Scenario: Check Webhooks in Proxy
    Given I have configured revizor environment:
      | name           | value          |
      | platform       | gce            |
      | dist           | ubuntu1404     |
      | branch         | master         |
    And I add role to this farm
    Then I expect server bootstrapping as P1
    And I execute local script 'https://git.io/vA52O' synchronous on P1
    And I set proxy for system.webhooks in Scalr to P1
    Then I restart service "workflow-engine"
    And I restart service "zmq_service"
    And Scalr services zmq_service,workflow-engine are in RUNNING state
    And Scalr services dbqueue are in STOPPED state
    Then I add F1 webhooks to Scalr:
      | schema | endpoint    | trigger_event | name           |
      | http   | /           | AccountEvent  | http_normal    |
      | https  | /           | AccountEvent  | https_normal   |
    When I execute 'szradm --fire-event AccountEvent' in F1
    And I assert F1 webhook results:
      | webhook_name   | expected_response | attempts | error |
      | http_normal    | 200               | 1        |       |
      | http_normal    | 200               | 1        |       |
    And proxy P1 log contains message "CONNECT" for F1
    And no "Traceback" in service "workflow-engine" log


  Scenario: Check Webhooks with ssl_verify=true
    Given I have configured scalr config:
        | name                                             | value |
        | scalr.system.webhooks.scalr_labs_workflow_engine | true  |
        | scalr.system.webhooks.ssl_verify                 | true  |
        | scalr.system.webhooks.retry_interval             | 5     |
    Then I stop service "dbqueue"
    Then I restart service "workflow-engine"
    Then I restart service "zmq_service"
    And Scalr services zmq_service,workflow-engine are in RUNNING state
    And Scalr services dbqueue are in STOPPED state
    Then I add F1 webhooks to Scalr:
      | schema | endpoint    | trigger_event | name          |
      | http   | /           | AccountEvent  | http_normal   |
      | http   | /redirect   | AccountEvent  | http_redirect |
      | http   | /abort404   | AccountEvent  | http_404      |
      | http   | /abort500   | AccountEvent  | http_500      |
      | http   | /retry      | AccountEvent  | http_retry    |
      | https  | /           | AccountEvent  | https_normal  |
    When I execute 'szradm --fire-event AccountEvent' in F1
    And I assert F1 webhook results:
      | webhook_name  | expected_response | attempts |         error             |
      | http_normal   | 200               | 1        |                           |
      | http_redirect | 200               | 1        |                           |
      | http_404      | 404               | 1        |                           |
      | http_500      | 500               | 2        |                           |
      | http_retry    | 200               | 2        |                           |
      | https_normal  | None              | 2        | certificate verify failed |
    And no "Traceback" in service "workflow-engine" log
