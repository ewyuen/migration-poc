"""Test Writer Agent: Coordinates reading skeleton files, introspecting services, and filling test bodies"""
import re
import os
from typing import Dict, List, Tuple, Any, Optional
from agents.test_writer.skeleton_reader import SkeletonReader
from agents.test_writer.service_introspector_csharp import ServiceIntrospectorCSharp
from agents.test_writer.gherkin_code_mapper import GherkinCodeMapper
from agents.test_writer.test_code_filler_csharp import TestCodeFillerCSharp
from agents.test_writer.fixture_generator import FixtureGenerator


class TestWriterAgent:
    """Orchestrates the conversion of test skeletons into fully-implemented C# tests"""

    def __init__(self):
        self.reader = SkeletonReader()
        self.introspector = ServiceIntrospectorCSharp()
        self.mapper = GherkinCodeMapper(self.introspector)
        self.filler = TestCodeFillerCSharp(self.mapper)
        self.fixture_gen = FixtureGenerator(self.introspector)

    def write_tests(self, skeleton_file_path: str, service_dir_path: str, output_file_path: str = None) -> Tuple[bool, str, str]:
        """
        Converts C# test skeletons into fully implemented tests using introspected service code.
        
        Returns:
            Tuple of (success, error_message, generated_code)
        """
        try:
            if not os.path.exists(skeleton_file_path):
                return False, f"Skeleton file not found: {skeleton_file_path}", ""

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

            # 2. Read skeleton file
            content = self.reader.read_csharp_skeleton(skeleton_file_path)
            class_info = self.reader.extract_test_class_info(content)
            methods = self.reader.extract_test_methods(content)

            # 3. Generate fully implemented method bodies
            # Replace methods in descending order of start_idx to keep offsets correct
            methods.sort(key=lambda x: x["start_idx"], reverse=True)
            
            modified_content = content
            for m in methods:
                m_name = m["name"]
                m_body = m["body"]
                m_header = m["header"]
                
                # Generate new method body
                new_body = self.filler.fill_test_method(m_name, m_body, m_header)
                
                # If the body contains "await", make the method async
                if "await" in new_body and "public void" in m_header:
                    m_header = m_header.replace("public void", "public async Task")

                # Format replacement
                replacement = f"{m_header}\n        {{\n{new_body}\n        }}"
                
                start = m["start_idx"]
                end = m["end_idx"]
                modified_content = modified_content[:start] + replacement + modified_content[end:]

            # 4. Generate and replace TestFixture class
            fixture_code = self.fixture_gen.generate_fixture(service_class, class_info["namespace"])
            
            # Find and replace TestFixture class block in modified_content
            fixture_match = re.search(r'public\s+class\s+TestFixture', modified_content)
            if fixture_match:
                f_start = fixture_match.start()
                open_brace_idx = modified_content.find('{', f_start)
                if open_brace_idx != -1:
                    close_brace_idx = SkeletonReader.find_matching_brace(modified_content, open_brace_idx)
                    if close_brace_idx != -1:
                        # Replace from public class TestFixture to its closing brace
                        modified_content = modified_content[:f_start] + fixture_code + modified_content[close_brace_idx + 1:]

            # 5. Add missing using statements if necessary
            # Make sure Task-based async tests have required imports
            required_usings = [
                "using System.Threading.Tasks;",
                "using System.Collections.Generic;",
                "using System.Linq;"
            ]
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
