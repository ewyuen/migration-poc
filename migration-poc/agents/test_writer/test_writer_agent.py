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

    def heal_tests(self, test_file_path: str, service_dir_path: str, errors: List[str]) -> Tuple[bool, str, str]:
        """
        Uses LLM to heal and correct compilation errors in a C# test file.
        """
        try:
            if not os.path.exists(test_file_path):
                return False, f"Test file not found: {test_file_path}", ""
                
            # 1. Read existing test file content
            with open(test_file_path, "r", encoding="utf-8") as f:
                current_test_code = f.read()

            # 2. Gather service class code in service_dir_path for LLM context
            service_files_content = ""
            for root, _, files in os.walk(service_dir_path):
                for file in files:
                    if file.endswith(".cs") and not file.endswith("Tests.cs") and not file.endswith(".Tests.cs"):
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, "r", encoding="utf-8") as sf:
                                service_files_content += f"// File: {file}\n" + sf.read() + "\n\n"
                        except Exception as e:
                            pass

            # 3. Build prompt
            errors_str = "\n".join([f"- {err}" for err in errors])
            prompt = f"""
You are an expert C# developer. We generated a unit test suite, but compilation failed with the following MSBuild errors:

COMPILATION ERRORS:
{errors_str}

CURRENT TEST CODE:
```csharp
{current_test_code}
```

MIGRATED SERVICE COMPONENT CODE:
```csharp
{service_files_content}
```

INSTRUCTIONS:
1. Analyze the compilation errors and correct the syntax, namespace, parameter types, or variables in the CURRENT TEST CODE.
2. Ensure the returned code is valid, compilable C# targeting .NET 10 with xUnit and FluentAssertions.
3. Do not modify the test scenarios or Gherkin intent; only fix the compilation errors.
4. Critical FluentAssertions Rule: If a variable or property has type 'bool' (boolean), you cannot assert it with `.Should().NotBeNull()`. This results in CS1061. You MUST assert booleans with `.Should().BeTrue()` or `.Should().BeFalse()`.
5. Return ONLY the complete corrected C# test file content. Do not include markdown code block syntax (like ```csharp) or explanations. Just return the raw code.
"""

            system = "You are a C# compilation correction agent. You only output corrected C# source code."

            print(f"🔧 TestWriter: Healing compile errors in {os.path.basename(test_file_path)} using LLM...")
            from llm_client import call_llm
            healed_code = call_llm(prompt, system, max_tokens=3000)

            # Strip any markdown backticks if LLM mistakenly returned them
            healed_code = healed_code.strip()
            if healed_code.startswith("```csharp"):
                healed_code = healed_code[len("```csharp"):].strip()
            if healed_code.startswith("```"):
                healed_code = healed_code[len("```"):].strip()
            if healed_code.endswith("```"):
                healed_code = healed_code[:-3].strip()

            # 4. Save corrected test code back
            with open(test_file_path, "w", encoding="utf-8") as f:
                f.write(healed_code)

            return True, "", healed_code

        except Exception as e:
            return False, f"Test healing failed: {str(e)}", ""
