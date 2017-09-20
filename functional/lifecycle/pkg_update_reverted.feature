Using step definitions from: steps/common_steps, steps/new_szr_upd_system, steps/import_steps
Feature: New scalarizr update policy test for broke the system with postinstall/fatal error

    @ec2 @gce @cloudstack @rackspaceng @openstack @import
    Scenario: Import server with scalarizr installed from branch
        Given I have a server running in cloud
        Then I install scalarizr to the server
        Then I trigger the Start building and run scalarizr
        And connection with scalarizr was established
        Then I trigger the Create role
        And Role has successfully been created

    @ec2 @gce @cloudstack @rackspaceng @openstack @import
    Scenario: Using new role
        Given I have a an empty running farm
        When I add to farm imported role
        Then I expect server bootstrapping as M1
        And scalarizr version is last in M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Bootstrap old scalarizr
        Given I have a an empty running farm
        When I add role to this farm with branch_custom
        Then I expect server bootstrapping as M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Update to new
        Given I have reverted and working branch
        When new package is builded
        Then I change branch to system for role
        And change branch in server M1 in sources to system
        And I update scalarizr via old api on M1
        When update process is finished on M1 with status completed
        Then Scalr receives HostUpdate from M1
        Then I push an empty commit to scalarizr repo
        And new package is builded
        Then I update scalarizr via api on M1
        And update process is finished on M1 with status completed
        And Scalr receives HostUpdate from M1
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

    @ec2 @cloudstack @rackspaceng @reboot
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

    @ec2 @cloudstack @rackspaceng @reboot
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
        And Scalr receives HostUpdate from M1
        Then scalarizr version is last in M1
        And scalarizr is running on M1
        And scalr-upd-client is running on M1

    @ec2 @gce @cloudstack @rackspaceng @openstack
    Scenario: Verify auto-update cron work
        When I remember scalarizr version on M1
        Given I have reverted and working branch
        And I push an empty commit to scalarizr repo
        When new package is builded
        Then wait 25 minutes for scalarizr auto updates on M1
        Then update process is finished on M1 with status completed
        And Scalr receives HostUpdate from M1
        And scalarizr version is last in M1
        And scalarizr is running on M1
        And scalr-upd-client is running on M1