Feature: PostgreSQL check user perms

    Scenario: Bootstraping role
        Given I have a an empty running farm
        When I add postgresql role to this farm
        Then I expect server bootstrapping as M1
        And postgresql is running on M1

    Scenario: Setup replication
        When I increase minimum servers to 2 for postgresql role
        Then I expect server bootstrapping as M2
        And M2 is slave of M1

    Scenario: Bootstraping base role
        When I add base role to this farm
        Then I expect server bootstrapping as B1

    Scenario: Check permissions
        Then I install postgresql client to <source>
        And I can connect to postgresql from <source> to <dest>

    Examples:
        | source | dest |
        | B1     | M1   |
        | B1     | M2   |
        | M1     | M2   |
        | M2     | M1   |