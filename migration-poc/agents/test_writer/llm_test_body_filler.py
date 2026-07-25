"""LLM Test Body Filler: Fills C# test method bodies via LLM, grounded strictly in real introspected interfaces"""
import re
from typing import Dict, List, Optional, Set

from llm_client import call_llm
from agents.test_writer.gherkin_extractor import GherkinExtractor
from agents.test_writer.service_introspector_csharp import ServiceIntrospectorCSharp


class LLMTestBodyFiller:
    """Fills the body of C# test methods with LLM-generated code, grounded in the real Stage-4 service surface"""

    def __init__(self, introspector: ServiceIntrospectorCSharp):
        self.introspector = introspector
        self.extractor = GherkinExtractor()

    def fill_test_method(
        self,
        method_name: str,
        method_body: str,
        header: str,
        service_class: str,
        fixture_code: str,
        feedback_errors: Optional[List[str]] = None,
        previous_body: Optional[str] = None,
    ) -> str:
        """
        Generate a fully implemented C# test method body via LLM, grounded strictly in the
        real introspected service surface and the actual generated test fixture surface.

        Returns indented method body text. Falls back to a clearly-marked placeholder body
        on any LLM/validation failure so one bad method never blocks the rest of the file.
        """
        steps = self.extractor.extract_steps_by_section(method_body)
        service_surface = self._build_service_surface(service_class)
        known = self._known_members(service_class, fixture_code)

        retry_section = ""
        if feedback_errors:
            errors_text = "\n".join(f"- {e}" for e in feedback_errors[:10])
            retry_section = f"""
### PREVIOUS ATTEMPT FAILED TO COMPILE
Previous body:
```csharp
{previous_body or "(unavailable)"}
```
Compiler errors:
{errors_text}

Fix ONLY these errors. Do not introduce any member that isn't in the ALLOWED SERVICE SURFACE or ALLOWED TEST FIXTURE SURFACE below.
"""

        prompt = f"""Implement the body of this C# xUnit test method.

### ALLOWED SERVICE SURFACE (the only service-side members you may reference)
{service_surface}

### ALLOWED TEST FIXTURE SURFACE (the only `_fixture.X` members you may reference)
```csharp
{fixture_code}
```

### TEST METHOD SIGNATURE
{header}

### GIVEN/WHEN/THEN STEPS
Given: {steps['given']}
When: {steps['when']}
Then: {steps['then']}
{retry_section}
### INSTRUCTIONS
1. Implement Arrange (Given), Act (When), Assert (Then) sections using ONLY members listed above.
2. Never invent classes, methods, properties, or fields that are not explicitly shown above. This includes request/response DTOs: only construct `new X(...)` for a type listed under DTOs/records above, the service class itself, or a plain built-in .NET type (Dictionary, List, TimeSpan, DateTime, Guid, etc.) -- never invent a new DTO type name.
3. If a step has no corresponding real member, express it as a plain local variable or a `// TODO:` comment instead of calling something that doesn't exist.
4. Construct the system under test with exactly `var systemUnderTest = _fixture.CreateSystemUnderTest();`, and call methods on it using EXACTLY the method names and parameter types/order shown in the ALLOWED SERVICE SURFACE (e.g. if a method takes a single DTO parameter, construct that DTO and pass it -- do not pass individual fields instead).
5. `await` any async service calls.
6. Use FluentAssertions style (`.Should()...`) for assertions, consistent with the rest of the file.
7. Respect the method signature above exactly (including any [Theory]/[InlineData] parameters already in scope).
8. Output ONLY the method body statements (no method signature, no surrounding braces) inside a single ```csharp fenced block. No explanations.
"""

        system = """You are a senior .NET test engineer. You may only reference members explicitly listed as available.
Never invent classes, methods, properties, or fields that are not shown to you. If in doubt, prefer a plain local variable or a TODO comment over a fabricated call."""

        try:
            response = call_llm(prompt, system, max_tokens=1200, temperature=0.2)
        except Exception as e:
            return self._fallback_body(f"LLM call failed: {e}")

        body = self._extract_csharp_code(response)
        if not body:
            return self._fallback_body("LLM returned an empty/unparseable response")

        validation_error = self._validate_body(body, known)
        if validation_error:
            return self._fallback_body(validation_error)

        return self._indent_body(body)

    def _build_service_surface(self, service_class: str) -> str:
        """Serialize the real service class + related records into a compact 'allowed members' block"""
        lines = [f"Service class: {service_class}"]

        constructor = self.introspector.find_constructor(service_class)
        ctor_params = ", ".join(f"{p['type']} {p['name']}" for p in constructor)
        lines.append(f"  Constructor: {service_class}({ctor_params})")

        methods = self.introspector.discover_methods(service_class)
        lines.append("  Public methods:")
        for m in methods:
            params = ", ".join(f"{p['type']} {p['name']}" for p in m["parameters"])
            async_kw = "async " if m["is_async"] else ""
            lines.append(f"    {async_kw}{m['return_type']} {m['name']}({params})")

        if self.introspector.records:
            lines.append("  DTOs/records:")
            for record_name, fields in self.introspector.records.items():
                field_str = ", ".join(f"{f['type']} {f['name']}" for f in fields)
                lines.append(f"    record {record_name}({field_str})")

        return "\n".join(lines)

    # Common BCL/framework types that are always safe to `new` up, even though they're not
    # part of the introspected Stage-4 grounding context.
    _SAFE_BUILTIN_TYPES = {
        "Dictionary", "List", "HashSet", "Queue", "Stack", "Exception", "InvalidOperationException",
        "ArgumentException", "ArgumentNullException", "NotImplementedException", "TimeSpan", "DateTime",
        "DateTimeOffset", "Guid", "StringBuilder", "Random", "Task", "ConfigurationBuilder", "Uri",
        "TaskCompletionSource",
    }

    def _known_members(self, service_class: str, fixture_code: str) -> Dict[str, Set[str]]:
        """Build the sets of real member/type names the LLM is allowed to reference"""
        service_methods = {m["name"] for m in self.introspector.discover_methods(service_class)}

        # Fixture members: public properties and methods exposed on TestFixture (e.g. `public FakeX Prop { get; }`,
        # `public AuthenticationService CreateSystemUnderTest()`)
        fixture_members = set(re.findall(r'public\s+[\w<>\.\[\],]+\s+(\w+)\s*\{', fixture_code))
        fixture_members |= set(re.findall(r'public\s+[\w<>\.\[\],]+\s+(\w+)\s*\(', fixture_code))

        record_names = set(self.introspector.records.keys())

        return {"service": service_methods, "fixture": fixture_members, "records": record_names, "service_class": {service_class}}

    def _validate_body(self, body: str, known: Dict[str, Set[str]]) -> Optional[str]:
        """Return an error string if the body references a member/type outside the known set, else None"""
        for member in re.findall(r'_fixture\.(\w+)', body):
            if member not in known["fixture"]:
                return f"references unknown fixture member '_fixture.{member}'"

        # Validate calls on the system-under-test regardless of what the LLM named the variable
        # (don't just look for a literal "systemUnderTest." -- the LLM may name it "sut" etc.)
        sut_var_match = re.search(r'\b(\w+)\s*=\s*_fixture\.CreateSystemUnderTest\s*\(\s*\)', body)
        if sut_var_match:
            sut_var = sut_var_match.group(1)
            for method in re.findall(rf'\b{re.escape(sut_var)}\.(\w+)\s*\(', body):
                if method not in known["service"]:
                    return f"references unknown service method '{sut_var}.{method}(...)'"

        # Validate any constructed type is either a known DTO/record, the service class itself,
        # or a common BCL type -- catches fabricated request/response DTOs like "UserCredentials".
        for type_name in re.findall(r'\bnew\s+(\w+)\s*[\(<]', body):
            if type_name in known["records"] or type_name in known["service_class"]:
                continue
            if type_name in self._SAFE_BUILTIN_TYPES:
                continue
            return f"constructs unknown type 'new {type_name}(...)' which is not a known record/DTO"

        return None

    def _extract_csharp_code(self, response: str) -> str:
        """Extract C# code from a fenced markdown response. Requires the fence -- an
        unfenced response is not trustworthy enough to treat as code and is rejected
        by the caller instead of being accepted as-is."""
        pattern = r"```csharp\s*(.*?)\s*```"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def _indent_body(self, body: str) -> str:
        return "\n".join(f"            {line}" if line.strip() else line for line in body.split("\n"))

    def _fallback_body(self, reason: str) -> str:
        safe_reason = reason.replace('"', "'")
        return (
            f"            // LLM_FILL_FAILED: {reason}\n"
            f'            Assert.Fail("Test body could not be generated: {safe_reason}");'
        )
