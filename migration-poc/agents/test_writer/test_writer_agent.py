"""Test Writer Agent: Coordinates reading skeleton files, introspecting services, and filling test bodies"""
import re
import os
from typing import Dict, List, Tuple, Optional
from agents.test_writer.skeleton_reader import SkeletonReader
from agents.test_writer.service_introspector_csharp import ServiceIntrospectorCSharp
from agents.test_writer.llm_test_body_filler import LLMTestBodyFiller
from agents.test_writer.fixture_generator import FixtureGenerator


class TestWriterAgent:
    """Orchestrates the conversion of test skeletons into fully-implemented C# tests"""

    def __init__(self):
        self.reader = SkeletonReader()
        self.introspector = ServiceIntrospectorCSharp()
        self.filler = LLMTestBodyFiller(self.introspector)
        self.fixture_gen = FixtureGenerator(self.introspector)

    def write_tests(
        self,
        skeleton_file_path: str,
        service_dir_path: str,
        output_file_path: str = None,
        skeleton_content: Optional[str] = None,
        feedback_errors: Optional[Dict[str, List[str]]] = None,
    ) -> Tuple[bool, str, str]:
        """
        Converts C# test skeletons into fully implemented tests using introspected service code
        and an LLM grounded strictly in the real introspected members.

        Args:
            skeleton_file_path: Path to the skeleton file (used as fallback source and as the
                default output path).
            service_dir_path: Directory containing the migrated (Stage 4) service source.
            output_file_path: Where to write the filled test file.
            skeleton_content: The pristine skeleton content to fill from. When provided, this is
                ALWAYS used as the source text instead of re-reading skeleton_file_path -- this
                guarantees every retry attempt composes fresh from the original skeleton rather
                than the previous attempt's (possibly already-filled) output.
            feedback_errors: Optional mapping of method_name -> list of compiler error strings
                from the previous failed attempt, used to steer the LLM's retry.

        Returns:
            Tuple of (success, error_message, generated_code)
        """
        try:
            if skeleton_content is None and not os.path.exists(skeleton_file_path):
                return False, f"Skeleton file not found: {skeleton_file_path}", ""

            feedback_errors = feedback_errors or {}

            # 1. Introspect service code
            self.introspector.introspect_directory(service_dir_path)

            # Identify the main service class under test (e.g. AuthenticationService)
            service_classes = self.introspector.discover_classes()
            if not service_classes:
                return False, f"No C# classes discovered in service directory: {service_dir_path}", ""

            # Find the service class matching "Service" or select the first class
            service_class = None
            for sc in service_classes:
                if "service" in sc.lower():
                    service_class = sc
                    break
            if not service_class:
                service_class = service_classes[0]

            # 2. Read skeleton content. ALWAYS prefer the pristine in-memory skeleton when
            # provided -- never re-read a previous attempt's output -- so nothing accumulates
            # across self-healing retries.
            content = skeleton_content if skeleton_content is not None else self.reader.read_csharp_skeleton(skeleton_file_path)
            class_info = self.reader.extract_test_class_info(content)

            # 3. Generate the TestFixture/Fake* code from real introspected source FIRST, and
            # replace the skeleton's TestFixture placeholder with it. This must happen before
            # method filling so the LLM filler can be given the actual fixture surface as
            # grounding context (it needs to know what `_fixture.X` members really exist).
            fixture_code = self.fixture_gen.generate_fixture(service_class, class_info["namespace"])

            fixture_match = re.search(r'public\s+class\s+TestFixture', content)
            if fixture_match:
                f_start = fixture_match.start()
                open_brace_idx = content.find('{', f_start)
                if open_brace_idx != -1:
                    close_brace_idx = SkeletonReader.find_matching_brace(content, open_brace_idx)
                    if close_brace_idx != -1:
                        content = content[:f_start] + fixture_code + content[close_brace_idx + 1:]

            # 4. Fill each test method body via the LLM (descending offset order keeps earlier
            # offsets valid as we splice replacements in).
            methods = self.reader.extract_test_methods(content)
            methods.sort(key=lambda x: x["start_idx"], reverse=True)

            modified_content = content
            for m in methods:
                m_name = m["name"]
                m_body = m["body"]
                m_header = m["header"]

                new_body = self.filler.fill_test_method(
                    m_name,
                    m_body,
                    m_header,
                    service_class,
                    fixture_code,
                    feedback_errors=feedback_errors.get(m_name),
                )

                # If the body contains "await", make the method async
                if "await" in new_body and "public void" in m_header:
                    m_header = m_header.replace("public void", "public async Task")

                # Format replacement
                replacement = f"{m_header}\n        {{\n{new_body}\n        }}"

                start = m["start_idx"]
                end = m["end_idx"]
                modified_content = modified_content[:start] + replacement + modified_content[end:]

            # 5. Add missing using statements if necessary
            component_namespace = None
            namespace_match = re.search(r'namespace\s+(\w+)\.Tests', modified_content)
            if namespace_match:
                component_namespace = namespace_match.group(1)

            required_usings = [
                "using System;",
                "using System.Threading.Tasks;",
                "using System.Collections.Generic;",
                "using System.Linq;"
            ]
            if component_namespace:
                required_usings.append(f"using {component_namespace};")

            for ru in required_usings:
                if ru not in modified_content:
                    modified_content = ru + "\n" + modified_content

            # Save to output file
            target_path = output_file_path or skeleton_file_path
            os.makedirs(os.path.dirname(target_path) or ".", exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(modified_content)

            return True, "", modified_content

        except Exception as e:
            return False, f"Test generation failed: {str(e)}", ""
