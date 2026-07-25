"""Unit tests for C# Test Writer Agent components"""
import unittest
import os
import tempfile
import shutil
from agents.test_writer.skeleton_reader import SkeletonReader
from agents.test_writer.gherkin_extractor import GherkinExtractor
from agents.test_writer.service_introspector_csharp import ServiceIntrospectorCSharp
from agents.test_writer.assertion_builder import AssertionBuilder
from agents.test_writer.gherkin_code_mapper import GherkinCodeMapper
from agents.test_writer.fixture_generator import FixtureGenerator
from agents.test_writer.test_writer_agent import TestWriterAgent


class TestSkeletonReader(unittest.TestCase):
    def test_extract_info_and_methods(self):
        sample_code = """
        namespace MyNamespace.Tests
        {
            public class MyServiceTests : TestBase
            {
                [Fact]
                public void MyTestMethod()
                {
                    // Arrange (Given)
                    // a condition
                    
                    // Act (When)
                    // an action
                    
                    // Assert (Then)
                    // an expectation
                }
            }
            
            public class TestFixture
            {
                public void Dispose() {}
            }
        }
        """
        reader = SkeletonReader()
        class_info = reader.extract_test_class_info(sample_code)
        self.assertEqual(class_info["namespace"], "MyNamespace.Tests")
        self.assertEqual(class_info["class_name"], "MyServiceTests")
        self.assertEqual(class_info["base_class"], "TestBase")

        methods = reader.extract_test_methods(sample_code)
        self.assertEqual(len(methods), 1)
        self.assertEqual(methods[0]["name"], "MyTestMethod")
        self.assertIn("// Arrange (Given)", methods[0]["body"])


class TestGherkinExtractor(unittest.TestCase):
    def test_extract_steps_and_params(self):
        extractor = GherkinExtractor()
        body = """
            // Arrange (Given)
            // a user with email "doctor@clinic.com" and password "SecurePass123"
            // the account is not locked out
            
            // Act (When)
            // I authenticate the user
            
            // Assert (Then)
            // the authentication should succeed
        """
        steps = extractor.extract_steps_by_section(body)
        self.assertEqual(len(steps["given"]), 2)
        self.assertEqual(steps["given"][0], "a user with email \"doctor@clinic.com\" and password \"SecurePass123\"")
        self.assertEqual(steps["when"][0], "I authenticate the user")
        self.assertEqual(steps["then"][0], "the authentication should succeed")

        params = extractor.extract_parameters("a patient age 70")
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["value"], "70")
        self.assertEqual(params[0]["type"], "int")

        params = extractor.extract_parameters("medication cost $100.00")
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["value"], "100.00")
        self.assertEqual(params[0]["type"], "decimal")


class TestServiceIntrospector(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def test_introspection(self):
        service_code = """
        namespace MyService
        {
            public record AuthRequest(string Email, string Password);

            public class MyAuthenticationService
            {
                public MyAuthenticationService(IUserRepository repo) {}

                public async Task<bool> AuthenticateUserAsync(AuthRequest request)
                {
                    return true;
                }
            }
        }
        """
        file_path = os.path.join(self.temp_dir, "MyAuthenticationService.cs")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(service_code)

        introspector = ServiceIntrospectorCSharp()
        introspector.introspect_directory(self.temp_dir)

        classes = introspector.discover_classes()
        self.assertIn("MyAuthenticationService", classes)

        methods = introspector.discover_methods("MyAuthenticationService")
        self.assertEqual(len(methods), 1)
        self.assertEqual(methods[0]["name"], "AuthenticateUserAsync")
        self.assertEqual(methods[0]["return_type"], "Task<bool>")
        self.assertEqual(len(methods[0]["parameters"]), 1)
        self.assertEqual(methods[0]["parameters"][0]["type"], "AuthRequest")

        self.assertIn("AuthRequest", introspector.records)


class TestAssertionBuilder(unittest.TestCase):
    def test_build_assertion(self):
        builder = AssertionBuilder()
        self.assertEqual(
            builder.build_assertion("authentication should succeed"),
            "result.IsSuccess.Should().BeTrue();"
        )
        self.assertEqual(
            builder.build_assertion("authentication should fail"),
            "result.IsSuccess.Should().BeFalse();"
        )
        self.assertEqual(
            builder.build_assertion("the discount should be $15.00"),
            "result.Value.DiscountAmount.Should().Be(15.00m);"
        )


if __name__ == "__main__":
    unittest.main()
