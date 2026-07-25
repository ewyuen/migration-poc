## Why

The Agilent Software Modernization Enablement Lead Engineer role requires demonstrating mastery of **multi-agent AI workflows for code extraction, logic migration, and test generation** in regulated medical environments. This POC establishes a working methodology for using sequential agentic orchestration to safely and auditably modernize legacy C# code to .NET 10, with emphasis on 21 CFR Part 11 compliance verification and Human-in-the-Loop quality gates. This methodology will form the foundation for scaling from single-component extraction to enterprise-wide legacy modernization pipelines.

## What Changes

- **New local multi-agent orchestration framework** using Python + OpenRouter + DeepSeek
  - Orchestrator Agent (coordinates workflow)
  - Explorer Agent (analyzes legacy code, identifies refactoring opportunities)
  - Extractor Agent (extracts pure domain logic and algorithms)
  - Modernizer Agent (translates to .NET 10 with modern patterns)
  - BDD Test Agent (generates Gherkin BDD test scenarios)
  - Verifier Agent (validates correctness, compliance, security)

- **Sequential agent execution** (Day 1)
  - Local Python scripts with transparent outputs
  - Each agent produces JSON/code/feature files
  - Results collected and analyzed before next agent runs

- **GitHub Actions workflow integration** (Day 2)
  - Wrap Python agents in GitHub Actions jobs
  - Add manual approval gate (Pull Request review)
  - Implement CFR Part 11 audit trail recording
  - Ready for production deployment pattern

- **OpenRouter + DeepSeek integration** for cost-effective LLM calls
  - ~$0.27 per 1M tokens (vs. Claude at $3-15)
  - Excellent code analysis capabilities
  - Suitable for POC and future enterprise deployments

## Capabilities

### New Capabilities

- `agentic-code-extraction`: Sequential multi-agent pipeline to analyze legacy code, identify refactoring opportunities, and plan modernization work
- `domain-logic-extraction`: Automatically extract pure, testable domain logic from legacy enterprise code, independent of infrastructure concerns
- `code-modernization-dotnet10`: Intelligent translation of legacy C# (.NET Framework) to modern .NET 10 with C# 14 patterns, async-first design, and dependency injection
- `bdd-test-generation`: Automatic generation of Gherkin BDD test scenarios from domain logic, including compliance-focused (CFR Part 11) test cases
- `agentic-verification`: Automated verification of code modernization including behavioral equivalence, test coverage analysis, compliance checks, and security scanning

### Modified Capabilities

<!-- No existing capabilities are being modified in this POC; we are introducing new agentic capabilities -->

## Impact

**Code**: 
- New `migration-poc/` directory with Python agents, orchestrator, and sample outputs
- Legacy code sample: `legacy-code/Observation.cs` (real medical component from mti-wpf)
- Generated outputs: Modern C# code, Gherkin feature files, verification reports

**Dependencies**:
- Python 3.8+
- `requests` library for OpenRouter API calls
- `python-dotenv` for environment configuration

**Systems**:
- Requires OpenRouter API access (free tier available)
- Produces portable artifacts (JSON, .cs files, .feature files)
- GitHub Actions workflow to be added (Day 2)

**Skills & Knowledge**:
- Demonstrates multi-agent orchestration patterns
- Shows domain-driven design (DDD) principles in code modernization
- Illustrates compliance-first architecture (CFR Part 11)
- Positions candidate for Agilent role requirements
