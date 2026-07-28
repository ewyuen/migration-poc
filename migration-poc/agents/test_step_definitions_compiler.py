"""Unit tests for step_definitions_compiler module (dotnet build error parsing)"""
import os
import tempfile
from unittest.mock import patch, Mock

from agents.step_definitions_compiler import StepDefinitionsCompiler


class TestParseErrors:
    def setup_method(self):
        self.compiler = StepDefinitionsCompiler()

    def test_parses_single_cs_error(self):
        stdout = "StepDefinitions.cs(12,9): error CS0103: The name 'foo' does not exist in the current context [tests.csproj]"
        errors = self.compiler._parse_errors(stdout, "")
        assert any("CS0103" in e for e in errors)
        assert any("StepDefinitions.cs(12,9)" in e for e in errors)

    def test_parses_multiple_errors(self):
        stdout = (
            "StepDefinitions.cs(10,5): error CS0103: The name 'bar' does not exist [tests.csproj]\n"
            "StepDefinitions.cs(20,1): error CS1002: ; expected [tests.csproj]\n"
        )
        errors = self.compiler._parse_errors(stdout, "")
        codes = "".join(errors)
        assert "CS0103" in codes
        assert "CS1002" in codes

    def test_no_errors_in_clean_output(self):
        stdout = "Build succeeded.\n0 Warning(s)\n0 Error(s)"
        errors = self.compiler._parse_errors(stdout, "")
        assert errors == []

    def test_errors_limited_to_ten(self):
        stdout = "\n".join(
            f"File.cs({i},1): error CS0103: problem {i} [tests.csproj]" for i in range(1, 20)
        )
        errors = self.compiler._parse_errors(stdout, "")
        assert len(errors) <= 10

    def test_errors_read_from_stderr_too(self):
        errors = self.compiler._parse_errors("", "File.cs(1,1): error CS9999: bad [tests.csproj]")
        assert any("CS9999" in e for e in errors)


class TestCompile:
    def test_missing_tests_dir_reports_failure_without_invoking_dotnet(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            compiler = StepDefinitionsCompiler(base_output_dir=tmpdir)
            with patch("agents.step_definitions_compiler.subprocess.run") as mock_run:
                result = compiler.compile("TestService", "nonexistent-run")
            mock_run.assert_not_called()
            assert result["success"] is False
            assert "Tests directory not found" in result["errors"][0]

    def test_successful_build_returns_success_true(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_id = "run1"
            tests_dir = os.path.join(tmpdir, run_id, "tests")
            os.makedirs(tests_dir)
            compiler = StepDefinitionsCompiler(base_output_dir=tmpdir)

            with patch("agents.step_definitions_compiler.subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0, stdout="Build succeeded.", stderr="")
                result = compiler.compile("TestService", run_id)

            assert result["success"] is True
            assert result["errors"] == []

    def test_failed_build_returns_parsed_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_id = "run1"
            tests_dir = os.path.join(tmpdir, run_id, "tests")
            os.makedirs(tests_dir)
            compiler = StepDefinitionsCompiler(base_output_dir=tmpdir)

            with patch("agents.step_definitions_compiler.subprocess.run") as mock_run:
                mock_run.return_value = Mock(
                    returncode=1,
                    stdout="StepDefinitions.cs(5,5): error CS0103: The name 'x' does not exist [tests.csproj]",
                    stderr="",
                )
                result = compiler.compile("TestService", run_id)

            assert result["success"] is False
            assert any("CS0103" in e for e in result["errors"])

    def test_timeout_reports_failure(self):
        import subprocess as sp
        with tempfile.TemporaryDirectory() as tmpdir:
            run_id = "run1"
            tests_dir = os.path.join(tmpdir, run_id, "tests")
            os.makedirs(tests_dir)
            compiler = StepDefinitionsCompiler(base_output_dir=tmpdir)

            with patch("agents.step_definitions_compiler.subprocess.run") as mock_run:
                mock_run.side_effect = sp.TimeoutExpired(cmd="dotnet build", timeout=60)
                result = compiler.compile("TestService", run_id)

            assert result["success"] is False
            assert "timed out" in result["errors"][0].lower()


class TestSaveToAudit:
    def test_writes_audit_log_with_status_and_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            compiler = StepDefinitionsCompiler()
            compile_result = {"success": False, "errors": ["CS0103 at File.cs(1,1): bad"], "raw_output": "full output"}
            compiler.save_to_audit(compile_result, "run1", tmpdir)

            audit_file = os.path.join(tmpdir, "step-definitions-compilation-run1.log")
            assert os.path.exists(audit_file)
            with open(audit_file, "r", encoding="utf-8") as f:
                content = f.read()
            assert "FAILED" in content
            assert "CS0103" in content
            assert "full output" in content
