"""Base test classes and utilities for generated tests across languages"""


class TestBaseClassGenerator:
    """Generates base test classes for different programming languages"""

    @staticmethod
    def generate_csharp_base() -> str:
        """Generate C# NUnit test base class"""
        return '''using NUnit.Framework;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace TestGenerated
{
    /// <summary>
    /// Base class for generated scenario tests using NUnit
    /// Provides common setup, utilities, and assertion helpers
    /// </summary>
    public class NUnitTestBase
    {
        /// <summary>
        /// Service client instance for test scenarios
        /// </summary>
        protected object ServiceClient { get; set; }

        /// <summary>
        /// Test context and state
        /// </summary>
        protected Dictionary<string, object> TestContext { get; set; }

        [SetUp]
        public virtual void SetUp()
        {
            TestContext = new Dictionary<string, object>();
        }

        [TearDown]
        public virtual void TearDown()
        {
            TestContext?.Clear();
        }

        /// <summary>
        /// Initialize service client for testing
        /// </summary>
        protected virtual void InitializeServiceClient(string serviceName)
        {
            // Override in derived classes
            TestContext["ServiceName"] = serviceName;
        }

        /// <summary>
        /// Assert response contains expected value
        /// </summary>
        protected void AssertResponseContains(object response, string key, object expectedValue)
        {
            Assert.That(response, Is.Not.Null, "Response should not be null");
            // Implementation depends on response type
        }

        /// <summary>
        /// Assert operation result
        /// </summary>
        protected void AssertOperationSuccessful(bool result, string message = "Operation should be successful")
        {
            Assert.That(result, Is.True, message);
        }

        /// <summary>
        /// Store test data for scenario
        /// </summary>
        protected void SetTestData(string key, object value)
        {
            TestContext[key] = value;
        }

        /// <summary>
        /// Retrieve test data from scenario
        /// </summary>
        protected object GetTestData(string key)
        {
            return TestContext.ContainsKey(key) ? TestContext[key] : null;
        }
    }
}
'''

    @staticmethod
    def generate_java_base() -> str:
        """Generate Java JUnit 5 test base class"""
        return '''package test.generated;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.DisplayName;
import static org.junit.jupiter.api.Assertions.*;

import java.util.HashMap;
import java.util.Map;

/**
 * Base class for generated scenario tests using JUnit 5
 * Provides common setup, utilities, and assertion helpers
 */
public class JUnitTestBase {
    /**
     * Service client instance for test scenarios
     */
    protected Object serviceClient;

    /**
     * Test context and state
     */
    protected Map<String, Object> testContext;

    @BeforeEach
    public void setUp() {
        testContext = new HashMap<>();
    }

    @AfterEach
    public void tearDown() {
        testContext.clear();
    }

    /**
     * Initialize service client for testing
     */
    protected void initializeServiceClient(String serviceName) {
        testContext.put("ServiceName", serviceName);
        // Override in derived classes
    }

    /**
     * Assert response contains expected value
     */
    protected void assertResponseContains(Object response, String key, Object expectedValue) {
        assertNotNull(response, "Response should not be null");
        // Implementation depends on response type
    }

    /**
     * Assert operation result
     */
    protected void assertOperationSuccessful(boolean result, String message) {
        assertTrue(result, message);
    }

    /**
     * Store test data for scenario
     */
    protected void setTestData(String key, Object value) {
        testContext.put(key, value);
    }

    /**
     * Retrieve test data from scenario
     */
    protected Object getTestData(String key) {
        return testContext.containsKey(key) ? testContext.get(key) : null;
    }
}
'''

    @staticmethod
    def generate_python_base() -> str:
        """Generate Python pytest test base class"""
        return '''"""Base class for generated scenario tests using pytest"""
import pytest
from typing import Any, Dict, Optional


class PytestTestBase:
    """
    Base class for generated scenario tests using pytest
    Provides common setup, utilities, and assertion helpers
    """

    def setup_method(self):
        """Setup for each test method"""
        self.service_client = None
        self.test_context: Dict[str, Any] = {}

    def teardown_method(self):
        """Teardown for each test method"""
        self.test_context.clear()

    def initialize_service_client(self, service_name: str) -> None:
        """
        Initialize service client for testing

        Args:
            service_name: Name of the service to initialize
        """
        self.test_context["ServiceName"] = service_name
        # Override in derived classes

    def assert_response_contains(self, response: Any, key: str, expected_value: Any) -> None:
        """
        Assert response contains expected value

        Args:
            response: Response object to validate
            key: Key to check in response
            expected_value: Expected value
        """
        assert response is not None, "Response should not be None"
        # Implementation depends on response type

    def assert_operation_successful(self, result: bool, message: str = "Operation should be successful") -> None:
        """
        Assert operation result

        Args:
            result: Boolean result to assert
            message: Error message if assertion fails
        """
        assert result, message

    def set_test_data(self, key: str, value: Any) -> None:
        """Store test data for scenario"""
        self.test_context[key] = value

    def get_test_data(self, key: str) -> Optional[Any]:
        """Retrieve test data from scenario"""
        return self.test_context.get(key)


# pytest fixtures for common operations
@pytest.fixture
def test_base():
    """Provide a test base instance"""
    return PytestTestBase()


@pytest.fixture
def gherkin_context():
    """Provide a context dictionary for Gherkin scenarios"""
    return {}
'''

    @staticmethod
    def generate_all_bases() -> dict:
        """Generate all base classes"""
        return {
            "csharp": TestBaseClassGenerator.generate_csharp_base(),
            "java": TestBaseClassGenerator.generate_java_base(),
            "python": TestBaseClassGenerator.generate_python_base(),
        }
