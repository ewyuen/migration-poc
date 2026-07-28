"""Step Definitions Enhancer: Uses LLM to fill step definition implementations"""
import logging
import re
from typing import Dict, Optional, Any
from llm_client import call_llm


def _strip_markdown_blocks(content: str) -> str:
    """Remove markdown code block syntax from content"""
    # Remove ```csharp...``` or ```cs...``` blocks
    content = re.sub(r'```\s*(csharp|cs|c#)\s*\n', '', content)
    content = re.sub(r'\n```\s*$', '', content)
    content = re.sub(r'\n```\s*\n', '\n', content)
    return content.strip()


class LLMContextBundleBuilder:
    """Build context bundle for LLM enhancement"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def build_context(
        self,
        skeleton: str,
        gherkin: str,
        modernized_code: Dict[str, str],
        exploration_results: Optional[Dict] = None
    ) -> Dict[str, str]:
        """Build full context for LLM"""
        return {
            'skeleton': skeleton,
            'gherkin': gherkin,
            'modernized_code': self._format_code(modernized_code),
            'domain_logic': exploration_results.get('key_patterns', '') if exploration_results else '',
            'compliance_rules': exploration_results.get('compliance_concerns', '') if exploration_results else ''
        }

    def _format_code(self, code_dict: Dict[str, str]) -> str:
        """Format modernized code for LLM prompt"""
        if not code_dict:
            return "// No modernized code available"

        formatted = []
        for filename, content in code_dict.items():
            # Limit to first 2000 chars per file to avoid token bloat
            truncated = content[:2000]
            if len(content) > 2000:
                truncated += "\n// ... (truncated)"
            formatted.append(f"// {filename}\n{truncated}")

        return "\n\n".join(formatted)


class StepDefinitionEnhancer:
    """Enhance step definition skeletons with LLM"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.context_builder = LLMContextBundleBuilder()

    def enhance(
        self,
        skeleton: str,
        gherkin: str,
        modernized_code: Dict[str, str],
        exploration_results: Optional[Dict] = None
    ) -> str:
        """Enhance step definition skeleton using LLM"""
        context = self.context_builder.build_context(
            skeleton, gherkin, modernized_code, exploration_results
        )

        prompt = self._build_prompt(context)
        system = self._build_system_prompt()

        self.logger.info("🧠 LLM Enhancer: Filling step definitions...")
        enhanced = call_llm(prompt, system, max_tokens=4000)
        enhanced = _strip_markdown_blocks(enhanced)
        self.logger.info("✅ LLM Enhancer: Step definitions enhanced")

        return enhanced

    def _build_prompt(self, context: Dict[str, str]) -> str:
        """Build LLM prompt for enhancement"""
        return f"""Fill in the TODO implementations in the step definitions file below.

SKELETON (with TODO placeholders):
{context['skeleton']}

GHERKIN SPECIFICATION (business intent):
{context['gherkin']}

MODERNIZED SERVICE CODE (available to call):
{context['modernized_code']}

DOMAIN RULES:
{context['domain_logic']}

COMPLIANCE CONCERNS:
{context['compliance_rules']}

INSTRUCTIONS:
1. Replace each // TODO with actual C# code
2. Use ScenarioContext["key"] to share state between steps
3. Call actual methods from the modernized code (only methods shown above)
4. Infer semantic key names for ScenarioContext (e.g., "CurrentUser", "AuthResult")
5. If a service is not shown in the code, generate a simple mock class
6. Keep implementations simple and testable
7. Never change method signatures or [Given/When/Then] attributes

IMPORTANT: Return ONLY the complete, compilable StepDefinitions.cs file. No markdown, no explanations."""

    def _build_system_prompt(self) -> str:
        """System prompt for LLM"""
        return """You are a C# and Reqnroll expert. You generate clean, testable step definitions for BDD tests.

Key expertise:
- Reqnroll [Binding], [Given], [When], [Then] attributes
- ScenarioContext for state sharing between steps
- Mock object generation for missing dependencies
- Semantic variable naming
- Minimal, focused implementations

Generate only valid, compilable C# code."""
