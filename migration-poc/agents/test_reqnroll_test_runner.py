"""Unit tests for reqnroll_test_runner scenario/output parsing"""
from agents.reqnroll_test_runner import ReqnrollTestRunner


class TestParseScenarios:
    def setup_method(self):
        self.runner = ReqnrollTestRunner()

    def test_parses_reqnroll_style_summary(self):
        output = "3 scenarios (1 failed, 2 passed)"
        scenarios = self.runner._parse_scenarios(output)
        assert scenarios == {"run": 3, "passed": 2, "failed": 1, "pending": 0}

    def test_parses_vstest_trailer_when_no_reqnroll_summary(self):
        # This is the format `dotnet test` actually prints by default (no Reqnroll-
        # specific "N scenarios (...)" line appears unless verbosity is raised).
        output = (
            "Passed!  - Failed:     0, Passed:     1, Skipped:     0, Total:     1, "
            "Duration: 443 ms - tests.dll (net10.0)"
        )
        scenarios = self.runner._parse_scenarios(output)
        assert scenarios == {"run": 1, "passed": 1, "failed": 0, "pending": 0}

    def test_parses_vstest_trailer_with_failures_and_skips(self):
        output = "Failed!  - Failed:     2, Passed:     3, Skipped:     1, Total:     6"
        scenarios = self.runner._parse_scenarios(output)
        assert scenarios == {"run": 6, "passed": 3, "failed": 2, "pending": 1}

    def test_no_match_returns_zeroed_counts(self):
        scenarios = self.runner._parse_scenarios("no useful output here")
        assert scenarios == {"run": 0, "passed": 0, "failed": 0, "pending": 0}


class TestParseStepFailures:
    def setup_method(self):
        self.runner = ReqnrollTestRunner()

    def test_extracts_step_binding_not_found(self):
        output = "Step binding not found for 'the login should succeed'"
        failures = self.runner._parse_step_failures(output)
        assert any("Step binding not found" in f for f in failures)

    def test_no_failures_in_clean_output(self):
        assert self.runner._parse_step_failures("Passed!  - Failed: 0, Passed: 1") == []
