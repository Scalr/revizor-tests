Using step definitions from: steps/pkg_update_steps, steps/import_steps, steps/lifecycle_steps, steps/scripting_steps, steps/new_szr_upd_system
Feature: Update scalarizr windows test

    @ui @legacy @msi_old @ec2 @gce @allow_clean_data
    Scenario Outline: Update from Scalr UI, windows test
      Given I have manually installed scalarizr '<default_agent>' on M1
      And scalarizr version is default in M1
      When I change branch for role
      And I trigger scalarizr update by Scalr UI on M1
      Then update process is finished on M1 with status completed
      And Scalr receives HostUpdate from M1
      And scalarizr version from role is last in M1
      When I execute script 'Windows ping-pong. CMD' synchronous on M1
      Then I see script result in M1
      And script output contains 'pong' in M1

    Examples:
      | default_agent |
      | 3.8.5         |
      | 3.12.7        |

    @manual @legacy @msi_old @ec2 @gce @allow_clean_data
    Scenario Outline: Manual scalarizr update, Windows test
      Given I have manually installed scalarizr '<default_agent>' on M2
      And scalarizr version is default in M2
      When I install new scalarizr to the server M2 manually
      Then update process is finished on M2 with status completed
      And Scalr receives HostUpdate from M2
      And scalarizr version from role is last in M2
      When I execute script 'Windows ping-pong. CMD' synchronous on M2
      Then I see script result in M2
      And script output contains 'pong' in M2

    Examples:
      | default_agent |
      | 3.8.5         |
      | 3.12.7        |

    @ui @rollback @legacy @ec2 @gce @allow_clean_data
    Scenario: Update from Scalr UI to corrupt package with rollback, Windows test
      Given I have manually installed scalarizr '3.8.5' on M3
      And scalarizr version is default in M3
      When I build corrupt package
      And I set branch with corrupt package for role
      When I trigger scalarizr update by Scalr UI on M3
      Then update process is finished on M3 with status rollbacked
      And scalarizr version is default in M3
      When I execute script 'Windows ping-pong. CMD' synchronous on M3
      Then I see script result in M3
      And script output contains 'pong' in M3

    @ui @rollback @legacy @ec2 @gce @allow_clean_data
    Scenario: Update from Scalr UI after rollback, Windows test
      Given I have manually installed scalarizr '3.8.5' on M4
      And scalarizr version is default in M4
      When I build corrupt package
      And I set branch with corrupt package for role
      When I trigger scalarizr update by Scalr UI on M4
      Then update process is finished on M4 with status rollbacked
      And scalarizr version is default in M4
      When I change branch for role
      And I trigger scalarizr update by Scalr UI on M4
      Then update process is finished on M4 with status completed
      And Scalr receives HostUpdate from M4
      And scalarizr version from role is last in M4
      When I execute script 'Windows ping-pong. CMD' synchronous on M4
      Then I see script result in M4
      And script output contains 'pong' in M4

    @manual @rollback @legacy @ec2 @gce @allow_clean_data
    Scenario: Manual scalarizr update to corrupt package with rollback, Windows test
      Given I have manually installed scalarizr '3.8.5' on M5
      And scalarizr version is default in M5
      When I build corrupt package
      And I install corrupt package to the server M5
      Then update process is finished on M5 with status rollbacked
      And scalarizr version is default in M5
      When I execute script 'Windows ping-pong. CMD' synchronous on M5
      Then I see script result in M5
      And script output contains 'pong' in M5

    @manual @rollback @legacy @ec2 @gce @allow_clean_data
    Scenario: Manual scalarizr update after rollback, Windows test
      Given I have manually installed scalarizr '3.8.5' on M6
      And scalarizr version is default in M6
      When I build corrupt package
      And I install corrupt package to the server M6
      Then update process is finished on M6 with status rollbacked
      And scalarizr version is default in M6
      When I install new scalarizr to the server M6 manually
      Then update process is finished on M6 with status completed
      And Scalr receives HostUpdate from M6
      And scalarizr version from role is last in M6
      When I execute script 'Windows ping-pong. CMD' synchronous on M6
      Then I see script result in M6
      And script output contains 'pong' in M6

    @ui @rollback @msi_old @ec2 @gce @allow_clean_data
    Scenario: Update from Scalr UI after corrupt package install, Windows test
      Given I have manually installed scalarizr '3.12.7' on M7
      And scalarizr version is default in M7
      When I build corrupt package
      And I set branch with corrupt package for role
      And I trigger scalarizr update by Scalr UI on M7
      Then update process is finished on M7 with status error
      When I change branch for role
      And I trigger scalarizr update by Scalr UI on M7
      Then update process is finished on M7 with status completed
      And Scalr receives HostUpdate from M7
      And scalarizr version from role is last in M7
      When I execute script 'Windows ping-pong. CMD' synchronous on M7
      Then I see script result in M7
      And script output contains 'pong' in M7

    @manual @rollback @msi_old @ec2 @gce @allow_clean_data
    Scenario: Manual scalarizr update after corrupt package install, Windows test
      Given I have manually installed scalarizr '3.12.7' on M8
      And scalarizr version is default in M8
      When I build corrupt package
      And I install corrupt package to the server M8
      Then update process is finished on M8 with status error
      When I install new scalarizr to the server M8 manually
      Then update process is finished on M8 with status completed
      And Scalr receives HostUpdate from M8
      And scalarizr version from role is last in M8
      When I execute script 'Windows ping-pong. CMD' synchronous on M8
      Then I see script result in M8
      And script output contains 'pong' in M8

    @manual @msi_new @ec2 @gce @allow_clean_data
    Scenario: Manual scalaizr update from msi_new to msi_new, Windows test
      Given I have manually installed scalarizr on M9
      And scalarizr version from role is last in M9
      And I save current Scalr update client version on M9
      When I build new package
      And I install new package to the server M9
      Then update process is finished on M9 with status completed
      And Scalr receives HostUpdate from M9
      And I check current Scalr update client version was changed on M9
      When I execute script 'Windows ping-pong. CMD' synchronous on M9
      Then I see script result in M9
      And script output contains 'pong' in M9

    @bootstrap @legacy @msi_old @ec2 @gce @allow_clean_data
    Scenario Outline: Update at bootstrap, windows test
      Given I have a server running in cloud
      When I install scalarizr <default_agent> with sysprep to the server
      Then I create image from deployed server
      And I add image to the new role
      When I have a an empty running farm
      And I add created role to the farm
      When I expect server bootstrapping as M10
      Then scalarizr version from role is last in M10
      When I execute script 'Windows ping-pong. CMD' synchronous on M10
      And I see script result in M10
      And script output contains 'pong' in M10

    Examples:
      | default_agent |
      | 3.8.5         |
      | 3.12.7        |

    @bootstrap @ui @msi_new @ec2 @gce @allow_clean_data
    Scenario: Update to corrupt package after bootstrap windows test, no prev updates
      Given I have a server running in cloud
      When I install scalarizr with sysprep to the server manually
      Then I create image from deployed server
      And I add image to the new role
      When I have a an empty running farm
      And I add created role to the farm
      And I change branch for role
      When I expect server bootstrapping as M11
      And scalarizr version from role is last in M11
      When I build corrupt package
      And I set branch with corrupt package for role
      And I trigger scalarizr update by Scalr UI on M11
      Then update process is finished on M11 with status error
      And scalarizr process is not running on M11
      And updclient process is running on M11

    @bootstrap @ui @msi_new @rollback @ec2 @gce @allow_clean_data
    Scenario: Update to corrupt package with rollback, windows test
      Given I have a server running in cloud
      When I install scalarizr with sysprep to the server manually
      Then I create image from deployed server
      And I add image to the new role
      When I have a an empty running farm
      And I add created role to the farm
      And I change branch for role
      When I expect server bootstrapping as M12
      And scalarizr version from role is last in M12
      When I build new package
      And I set branch with new package for role
      When I trigger scalarizr update by Scalr UI on M12
      Then update process is finished on M12 with status completed
      And Scalr receives HostUpdate from M12
      When I build corrupt package
      And I set branch with corrupt package for role
      When I trigger scalarizr update by Scalr UI on M12
      Then update process is finished on M12 with status rollbacked
      And scalarizr process is running on M12
      And updclient process is running on M12
      When I execute script 'Windows ping-pong. CMD' synchronous on M12
      Then I see script result in M12
      And script output contains 'pong' in M12
