Feature: Tomcat 6 and 7 test for CentOS

    @ec2 @gce @cloudstack @rackspaceng @tomcat7
    Scenario: Bootstraping tomcat7 role
        Given I have a an empty running farm
        When I add tomcat7 role to this farm
        Then I expect server bootstrapping as T1
        And 8080 port is listen on T1
        And 8443 port is listen on T1

    @ec2 @gce @cloudstack @rackspaceng @tomcat6
    Scenario: Bootstraping tomcat6 role
        Given I have a an empty running farm
        When I add tomcat6 role to this farm
        Then I expect server bootstrapping as T1
        And 8080 port is listen on T1
        And 8443 port is listen on T1