"""Unit tests for C# Test Writer Agent components"""
import unittest
import os
import tempfile
import shutil
from unittest.mock import patch
from agents.test_writer.skeleton_reader import SkeletonReader
from agents.test_writer.gherkin_extractor import GherkinExtractor
from agents.test_writer.service_introspector_csharp import ServiceIntrospectorCSharp
from agents.test_writer.fixture_generator import FixtureGenerator
from agents.test_writer.llm_test_body_filler import LLMTestBodyFiller
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

    def test_interface_methods_are_parsed(self):
        service_code = """
        namespace MyService
        {
            public interface IUserRepository
            {
                Task<bool> ValidateUserAsync(string email, string password);
                Task RecordFailedAttemptAsync(string email);
            }
        }
        """
        file_path = os.path.join(self.temp_dir, "IUserRepository.cs")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(service_code)

        introspector = ServiceIntrospectorCSharp()
        introspector.introspect_directory(self.temp_dir)

        methods = introspector.interfaces.get("IUserRepository", {}).get("methods", [])
        method_names = {m["name"] for m in methods}
        self.assertEqual(method_names, {"ValidateUserAsync", "RecordFailedAttemptAsync"})
        validate = next(m for m in methods if m["name"] == "ValidateUserAsync")
        self.assertEqual(validate["return_type"], "Task<bool>")
        self.assertEqual(len(validate["parameters"]), 2)


SAMPLE_TEST_FILE = """
namespace MyNamespace.Tests
{
    public class MyServiceTests
    {
        [Fact]
        public void PassingTest()
        {
            var x = 1;
        }

        [Fact]
        public void FailingTest()
        {
            var y = Broken.Reference;
        }
    }

    public class TestFixture
    {
        public void Dispose() {}
    }

    public class FakeUserRepository
    {
    }
}
"""


class TestSkeletonReaderClassesAndLocate(unittest.TestCase):
    def test_extract_test_classes_excludes_primary_test_class(self):
        reader = SkeletonReader()
        classes = reader.extract_test_classes(SAMPLE_TEST_FILE)
        names = {c["name"] for c in classes}
        self.assertEqual(names, {"TestFixture", "FakeUserRepository"})

    def test_locate_error_maps_line_to_method(self):
        reader = SkeletonReader()
        methods = reader.extract_test_methods(SAMPLE_TEST_FILE)
        classes = reader.extract_test_classes(SAMPLE_TEST_FILE)

        failing_line = next(
            i + 1 for i, line in enumerate(SAMPLE_TEST_FILE.split("\n"))
            if "Broken.Reference" in line
        )

        loc = SkeletonReader.locate_error(SAMPLE_TEST_FILE, methods, classes, failing_line)
        self.assertIsNotNone(loc)
        self.assertEqual(loc["kind"], "method")
        self.assertEqual(loc["name"], "FailingTest")

    def test_locate_error_maps_line_to_class(self):
        reader = SkeletonReader()
        methods = reader.extract_test_methods(SAMPLE_TEST_FILE)
        classes = reader.extract_test_classes(SAMPLE_TEST_FILE)

        fixture_line = next(
            i + 1 for i, line in enumerate(SAMPLE_TEST_FILE.split("\n"))
            if "public void Dispose" in line
        )

        loc = SkeletonReader.locate_error(SAMPLE_TEST_FILE, methods, classes, fixture_line)
        self.assertIsNotNone(loc)
        self.assertEqual(loc["kind"], "class")
        self.assertEqual(loc["name"], "TestFixture")


class TestFixtureGeneratorGenericFakes(unittest.TestCase):
    def test_generate_fake_class_uses_introspected_interface_methods(self):
        introspector = ServiceIntrospectorCSharp()
        introspector.interfaces["ISomeRepository"] = {
            "methods": [
                {"name": "GetValueAsync", "is_async": True, "return_type": "Task<int>", "parameters": []},
            ]
        }
        fixture_gen = FixtureGenerator(introspector)
        fake_code = fixture_gen._generate_fake_class("ISomeRepository")
        self.assertIn("class FakeSomeRepository", fake_code)
        self.assertIn("GetValueAsync", fake_code)

    def test_iconfiguration_gets_real_instance_not_a_fake(self):
        introspector = ServiceIntrospectorCSharp()
        introspector.classes["SomeService"] = {
            "constructor": [{"name": "configuration", "type": "IConfiguration"}],
            "methods": []
        }
        fixture_gen = FixtureGenerator(introspector)
        fixture_code = fixture_gen.generate_fixture("SomeService", "MyNamespace")
        self.assertIn("ConfigurationBuilder", fixture_code)
        self.assertNotIn("class FakeConfiguration", fixture_code)


class TestLLMTestBodyFillerFallback(unittest.TestCase):
    def setUp(self):
        self.introspector = ServiceIntrospectorCSharp()
        self.introspector.classes["MyService"] = {
            "constructor": [],
            "methods": [{"name": "DoWork", "is_async": True, "return_type": "Task<bool>", "parameters": []}]
        }
        self.filler = LLMTestBodyFiller(self.introspector)
        self.header = "public void MyTest()"
        self.body = "// Arrange (Given)\n// something\n// Act (When)\n// something else\n// Assert (Then)\n// result"
        self.fixture_code = "public class TestFixture { public MyService CreateSystemUnderTest() => new MyService(); }"

    @patch("agents.test_writer.llm_test_body_filler.call_llm")
    def test_falls_back_when_no_fenced_code_block(self, mock_call_llm):
        mock_call_llm.return_value = "I cannot help with that."
        result = self.filler.fill_test_method("MyTest", self.body, self.header, "MyService", self.fixture_code)
        self.assertIn("LLM_FILL_FAILED", result)

    @patch("agents.test_writer.llm_test_body_filler.call_llm")
    def test_falls_back_when_referencing_unknown_member(self, mock_call_llm):
        mock_call_llm.return_value = "```csharp\nvar result = _fixture.NotReal.DoSomething();\n```"
        result = self.filler.fill_test_method("MyTest", self.body, self.header, "MyService", self.fixture_code)
        self.assertIn("LLM_FILL_FAILED", result)

    @patch("agents.test_writer.llm_test_body_filler.call_llm")
    def test_accepts_valid_grounded_response(self, mock_call_llm):
        mock_call_llm.return_value = (
            "```csharp\n"
            "var systemUnderTest = _fixture.CreateSystemUnderTest();\n"
            "var result = await systemUnderTest.DoWork();\n"
            "result.Should().BeTrue();\n"
            "```"
        )
        result = self.filler.fill_test_method("MyTest", self.body, self.header, "MyService", self.fixture_code)
        self.assertNotIn("LLM_FILL_FAILED", result)
        self.assertIn("DoWork", result)


if __name__ == "__main__":
    unittest.main()
