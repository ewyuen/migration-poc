```gherkin
Feature: User Authentication and Session Management
  As a medical software system
  I want to authenticate users and manage sessions securely
  So that patient data remains protected and compliant with 21 CFR Part 11

  Background:
    Given the system is initialized
    And audit logging is enabled

  Scenario: Valid user authentication
    Given a user with email "user@test.com" and password "validPassword123"
    When I authenticate the user
    Then the authentication should succeed
    And an audit trail entry should be created

  Scenario Outline: Input validation failures
    Given a user with <email> and <password>
    When I try to authenticate the user
    Then the request should fail with error "Invalid inputs"

    Examples:
      | email          | password       |
      | ""             | "password123"  |
      | "user@test.com" | ""            |
      | ""             | ""            |

  Scenario: Valid session token generation
    Given a user with email "user@test.com"
    When I generate a session token
    Then a valid session token should be created
    And an audit trail entry should be created

  Scenario: Invalid session token validation
    Given an invalid session token "invalidToken"
    When I validate the session token
    Then the validation should fail

  Scenario: Age-based discount calculation for senior citizen
    Given a user with age 65
    And an amount of $100.00
    When I calculate the discount
    Then the discount should be $15.00

  Scenario: Age-based discount calculation for adult
    Given a user with age 30
    And an amount of $100.00
    When I calculate the discount
    Then the discount should be $5.00

  Scenario: Age-based discount calculation for minor
    Given a user with age 15
    And an amount of $100.00
    When I calculate the discount
    Then the discount should be $0.00

  Scenario Outline: Boundary values for age-based discount
    Given a user with age <age>
    And an amount of $100.00
    When I calculate the discount
    Then the discount should be <discount>

    Examples:
      | age | discount |
      | 64  | $5.00    |
      | 65  | $15.00   |
      | 21  | $5.00    |
      | 20  | $0.00    |

  Scenario: Admin user authentication
    Given an admin user with email "admin@test.com" and password "password123"
    When I authenticate the admin user
    Then the authentication should succeed
    And an audit trail entry should be created

  Scenario: Compliance audit trail recording
    Given a user with email "user@test.com" and password "validPassword123"
    When I authenticate the user
    Then an audit trail entry should be created with details "User authenticated: user@test.com"

  Scenario: Error scenario - invalid email format
    Given a user with email "invalidEmail" and password "password123"
    When I try to authenticate the user
    Then the request should fail with error "Invalid email format"

  Scenario: Error scenario - password too short
    Given a user with email "user@test.com" and password "short"
    When I try to authenticate the user
    Then the request should fail with error "Password must be at least 8 characters"

  Scenario: Error scenario - invalid age for discount
    Given a user with age -1
    And an amount of $100.00
    When I try to calculate the discount
    Then the request should fail with error "Age must be between 0 and 120"

  Scenario: Error scenario - invalid amount for discount
    Given a user with age 30
    And an amount of -$100.00
    When I try to calculate the discount
    Then the request should fail with error "Amount must be greater than or equal to 0"
```