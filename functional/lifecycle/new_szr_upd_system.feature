Using step definitions from: steps/common_steps, steps/new_szr_upd_system
Feature: New scalarizr update policy test for broke the system with postinstall/fatal error

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstraping
        Given I have reverted and working branch
        And I have a an empty running farm
        When I add role to this farm
        Then I expect server bootstrapping as M1
        Given I have reverted and working branch
        And I push an empty commit to scalarizr repo
        When new package is builded
        Then I update scalarizr via api on M1
        When update process is finished on M1 with status completed
        Then I remember scalarizr version on M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify broken postinstall script
        Given I have reverted and working branch
        When I broke branch with commit "@update-system @postinst"
        And new package is builded
        Then I update scalarizr via api on M1
        When update process is finished on M1 with status rollbacked
        Then scalarizr version is the same on M1
        And scalarizr is running on M1
        And scalr-upd-client is running on M1

    @ec2 @cloudstack @rackspaceng @eucalyptus @reboot
    Scenario: Reboot server
        When I reboot server M1
        And Scalr receives RebootFinish from M1
        Then scalarizr version is the same on M1
        And scalarizr is running on M1
        And scalr-upd-client is running on M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify broken with fatal error
        Given I have reverted and working branch
        When I broke branch with commit "@update-system @fatal-error"
        And new package is builded
        Then I update scalarizr via api on M1
        When update process is finished on M1 with status rollbacked
        Then scalarizr version is the same on M1
        And scalarizr is running on M1
        And scalr-upd-client is running on M1

    @ec2 @cloudstack @rackspaceng @eucalyptus @reboot
    Scenario: Reboot server
        When I reboot server M1
        And Scalr receives RebootFinish from M1
        Then scalarizr version is the same on M1
        And scalarizr is running on M1
        And scalr-upd-client is running on M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify scalr-upd-client update to normal version
        Given I have reverted and working branch
        And new package is builded
        Then I update scalarizr via api on M1
        When update process is finished on M1 with status completed
        Then scalarizr version is last in M1
        And scalarizr is running on M1
        And scalr-upd-client is running on M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify auto-update cron work
        When I remember scalarizr version on M1
        Given I have reverted and working branch
        And I push an empty commit to scalarizr repo
        When new package is builded
        Then wait 15 minutes for scalarizr auto updates on M1
        Then update process is finished on M1 with status completed
        And scalarizr version is last in M1
        And scalarizr is running on M1
        And scalr-upd-client is running on M1