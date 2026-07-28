"""Step Definitions Enhancer: Uses LLM to fill step definition implementations"""
import logging
import re
from typing import Dict, Optional, Any
from llm_client import call_llm


def _strip_markdown_blocks(content: str) -> str:
    """Remove markdown code block syntax and trailing prose from C# content"""
    # Remove ```csharp...``` or ```cs...``` blocks
    content = re.sub(r'```\s*(csharp|cs|c#)\s*\n', '', content)
    content = re.sub(r'\n```\s*$', '', content)
    content = re.sub(r'\n```\s*\n', '\n', content)

    lines = content.split('\n')

    # Find start of C# code (namespace or using)
    code_start_idx = -1
    for i, line in enumerate(lines):
        if line.strip().startswith(('using ', 'namespace ')):
            code_start_idx = i
            break

    if code_start_idx > 0:
        lines = lines[code_start_idx:]
    elif code_start_idx == -1:
        # No namespace found, look for class definition
        for i, line in enumerate(lines):
            if '[' in line and ('Binding' in line or 'Given' in line or 'When' in line or 'Then' in line):
                code_start_idx = i
                break
        if code_start_idx > 0:
            lines = lines[code_start_idx:]

    # Find last valid C# line and truncate after it
    # Valid C#: ends with closing brace, method, property, attribute, using, namespace
    last_valid_idx = -1
    brace_depth = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped:
            brace_depth += stripped.count('{') - stripped.count('}')
            # Keep lines that are code (have braces, keywords, or are indented)
            if (stripped.endswith(('{', '}', ';')) or
                stripped.startswith(('using ', 'namespace ', 'public ', 'private ', '[',
                                   'class ', 'void ', 'string ', 'int ', 'bool ', 'return')) or
                '{' in line or '}' in line):
                last_valid_idx = i
        elif brace_depth > 0:
            # Empty line inside code block
            last_valid_idx = i

    if last_valid_idx >= 0:
        lines = lines[:last_valid_idx + 1]

    return '\n'.join(lines).strip()


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
            # Truncating too aggressively silently hides real methods from the LLM,
            # causing it to hallucinate mock implementations instead of calling the
            # actual API (e.g. GenerateSessionToken() cut off -> LLM invents "mock-token").
            # 12000 chars comfortably covers typical single-service migration files.
            limit = 12000
            truncated = content[:limit]
            if len(content) > limit:
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
0. The skeleton above contains EVERY [Given]/[When]/[Then] method that must exist in your output — count
   them. Your output must contain the SAME NUMBER of bound methods, one per skeleton method, even if two
   methods look similar or redundant. Do NOT drop, merge, or silently omit any of them.
1. Replace each // TODO with actual C# code
2. Use ScenarioContext["key"] to share state between steps
3. Call ONLY methods/properties/fields that are EXPLICITLY defined in the modernized code shown above.
   NEVER invent a method, property, or public accessor that isn't there — this is the #1 cause of compile
   failures. Do not assume a getter exists for a private field. Do not guess at a method name because it
   "should" exist (e.g. do not call GetConnectionString() on the service unless that exact method is shown
   in MODERNIZED SERVICE CODE above).
4. Infer semantic key names for ScenarioContext (e.g., "CurrentUser", "AuthResult")
5. If a service is not shown in the code, generate a simple mock class
6. Keep implementations simple and testable
7. Never change method signatures or [Given/When/Then] attributes
8. If a Gherkin step needs to verify something that has NO corresponding public method/property in the
   modernized code (e.g. an internal/private field with no accessor), do NOT invent an API to reach it.
   Instead write the weakest assertion that is still true and compiles — e.g. assert construction succeeded
   without throwing, or assert on a value already exposed elsewhere — rather than calling a nonexistent member.

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
