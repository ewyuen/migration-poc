"""Step mapper: Map Gherkin steps to test code implementations"""
import re
import logging
from typing import Dict, List, Callable, Optional, Tuple
from dataclasses import dataclass


@dataclass
class StepMapping:
    """Represents a mapping from Gherkin step pattern to code"""
    pattern: str
    action: str
    description: str
    code_generator: Optional[Callable] = None


class StepRegistry:
    """Registry of Gherkin step patterns and their implementations"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mappings: Dict[str, List[StepMapping]] = {
            'service_init': [],
            'api_call': [],
            'assertion': [],
            'other': []
        }
        self.unmapped_steps: List[str] = []
        self._register_default_patterns()

    def _register_default_patterns(self):
        """Register common Gherkin step patterns"""
        # Service initialization patterns
        self.register_mapping(
            pattern=r"^(?:Given|When|Then)\s+(?:a|the)\s+(\w+)\s+service\s+is\s+(?:running|initialized)$",
            action="initialize_service",
            description="Initialize a service",
            category="service_init"
        )
        self.register_mapping(
            pattern=r"^(?:Given|When|Then)\s+(\w+)\s+service\s+client\s+is\s+set\s+up$",
            action="setup_service_client",
            description="Set up service client",
            category="service_init"
        )

        # API call patterns
        self.register_mapping(
            pattern=r"^(?:When)\s+I\s+(?:call|invoke|execute)\s+(\w+)\s+(?:on|with)\s+(.+)$",
            action="call_api",
            description="Call service API",
            category="api_call"
        )
        self.register_mapping(
            pattern=r"^(?:When)\s+(\w+)\s+(?:is\s+called|is\s+invoked)\s+(?:with|on)\s+(.+)$",
            action="call_api",
            description="Call service operation",
            category="api_call"
        )

        # Assertion patterns
        self.register_mapping(
            pattern=r"^(?:Then)\s+the\s+response\s+(?:should|must)\s+contain\s+(.+)$",
            action="assert_response_contains",
            description="Assert response contains value",
            category="assertion"
        )
        self.register_mapping(
            pattern=r"^(?:Then)\s+(.+)\s+(?:should|must)\s+be\s+(.+)$",
            action="assert_equals",
            description="Assert equality",
            category="assertion"
        )
        self.register_mapping(
            pattern=r"^(?:Then)\s+(?:I|the\s+system)\s+(?:receive|get|obtain)\s+(.+)$",
            action="assert_received",
            description="Assert received value",
            category="assertion"
        )

    def register_mapping(self, pattern: str, action: str, description: str,
                         category: str = "other", code_generator: Optional[Callable] = None):
        """
        Register a new step pattern mapping.

        Args:
            pattern: Regex pattern for step text
            action: Action identifier for code generation
            description: Human-readable description
            category: Category of the mapping
            code_generator: Optional callable to generate code
        """
        mapping = StepMapping(
            pattern=pattern,
            action=action,
            description=description,
            code_generator=code_generator
        )

        if category not in self.mappings:
            self.mappings[category] = []

        self.mappings[category].append(mapping)
        self.logger.debug(f"Registered pattern: {pattern} -> {action}")

    def find_mapping(self, step_text: str) -> Optional[StepMapping]:
        """
        Find a mapping for a Gherkin step.

        Args:
            step_text: The step text to match

        Returns:
            StepMapping if found, None otherwise
        """
        for category in self.mappings:
            for mapping in self.mappings[category]:
                if re.match(mapping.pattern, step_text):
                    self.logger.debug(f"Matched step: '{step_text}' -> {mapping.action}")
                    return mapping

        self.unmapped_steps.append(step_text)
        self.logger.warning(f"No mapping found for step: {step_text}")
        return None

    def find_all_mappings(self, step_text: str) -> List[StepMapping]:
        """Find all possible mappings for a step (for ambiguity detection)"""
        matches = []
        for category in self.mappings:
            for mapping in self.mappings[category]:
                if re.match(mapping.pattern, step_text):
                    matches.append(mapping)
        return matches

    def extract_step_params(self, step_text: str, mapping: StepMapping) -> List[str]:
        """
        Extract parameters from step text using the mapping pattern.

        Args:
            step_text: The step text
            mapping: The StepMapping with regex pattern

        Returns:
            List of extracted parameter values
        """
        match = re.match(mapping.pattern, step_text)
        if match:
            return list(match.groups())
        return []


class ServiceAPIIntrospector:
    """Introspect service APIs to inform step mapping"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.service_operations: Dict[str, List[str]] = {}

    def register_service_operations(self, service_name: str, operations: List[str]):
        """
        Register available operations for a service.

        Args:
            service_name: Name of the service
            operations: List of operation names (e.g., ['GetUser', 'CreateUser', 'UpdateUser'])
        """
        self.service_operations[service_name] = operations
        self.logger.info(f"Registered {len(operations)} operations for {service_name}")

    def get_service_operations(self, service_name: str) -> List[str]:
        """Get list of available operations for a service"""
        return self.service_operations.get(service_name, [])

    def infer_operation_from_step(self, service_name: str, step_text: str) -> Optional[str]:
        """
        Attempt to infer which service operation a step refers to.

        Args:
            service_name: Name of the service
            step_text: The step text

        Returns:
            Operation name if found, None otherwise
        """
        operations = self.get_service_operations(service_name)
        if not operations:
            return None

        step_lower = step_text.lower()
        for operation in operations:
            if operation.lower() in step_lower:
                return operation

        return None

    def infer_parameters_from_step(self, step_text: str) -> Dict[str, str]:
        """
        Extract parameters from step text (e.g., values in quotes or numbers).

        Args:
            step_text: The step text

        Returns:
            Dictionary of extracted parameters
        """
        params = {}

        # Extract quoted strings
        quoted_matches = re.findall(r'"([^"]*)"', step_text)
        for i, value in enumerate(quoted_matches):
            params[f"param_{i}"] = value

        # Extract numbers
        number_matches = re.findall(r'\b(\d+)\b', step_text)
        for i, value in enumerate(number_matches):
            params[f"number_{i}"] = value

        return params


class UnmappedStepHandler:
    """Handle steps that don't have explicit mappings"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def generate_placeholder_code(self, language: str, step_text: str,
                                  service_name: Optional[str] = None) -> str:
        """
        Generate placeholder test code for unmapped steps.

        Args:
            language: Target language (csharp, java, python)
            step_text: The Gherkin step text
            service_name: Optional service name

        Returns:
            Placeholder code
        """
        if language.lower() in ['csharp', 'c#']:
            return self._generate_csharp_placeholder(step_text)
        elif language.lower() == 'java':
            return self._generate_java_placeholder(step_text)
        elif language.lower() == 'python':
            return self._generate_python_placeholder(step_text)
        else:
            return self._generate_python_placeholder(step_text)

    @staticmethod
    def _generate_csharp_placeholder(step_text: str) -> str:
        """Generate C# placeholder for unmapped step"""
        method_name = UnmappedStepHandler._step_to_method_name(step_text)
        return f'''    [Test]
    public void {method_name}()
    {{
        // TODO: Implement step: {step_text}
        Assert.Inconclusive("Step not yet implemented");
    }}
'''

    @staticmethod
    def _generate_java_placeholder(step_text: str) -> str:
        """Generate Java placeholder for unmapped step"""
        method_name = UnmappedStepHandler._step_to_method_name(step_text)
        return f'''    @Test
    @DisplayName("{step_text}")
    public void {method_name}() {{
        // TODO: Implement step: {step_text}
        fail("Step not yet implemented");
    }}
'''

    @staticmethod
    def _generate_python_placeholder(step_text: str) -> str:
        """Generate Python placeholder for unmapped step"""
        method_name = UnmappedStepHandler._step_to_method_name(step_text)
        return f'''def test_{method_name}():
    """
    TODO: Implement step: {step_text}
    """
    pytest.skip("Step not yet implemented")
'''

    @staticmethod
    def _step_to_method_name(step_text: str) -> str:
        """Convert Gherkin step text to a valid method name"""
        # Remove Given/When/Then/And/But
        text = re.sub(r'^(Given|When|Then|And|But)\s+', '', step_text, flags=re.IGNORECASE)
        # Convert to snake_case
        text = re.sub(r'[^a-zA-Z0-9]+', '_', text)
        text = re.sub(r'^_|_$', '', text)  # Remove leading/trailing underscores
        text = re.sub(r'_+', '_', text)    # Remove multiple underscores
        return text.lower()
