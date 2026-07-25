"""Skeleton Reader: Read and parse C# skeleton test files"""
import re
from typing import Dict, List, Tuple, Optional


class SkeletonReader:
    """Reads and parses C# test files to extract structure and metadata"""

    @staticmethod
    def read_csharp_skeleton(filepath: str) -> str:
        """Reads C# skeleton file content"""
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    @staticmethod
    def find_matching_brace(text: str, start_idx: int) -> int:
        """Find the index of the matching closing brace '}' for the opening brace '{' at start_idx"""
        brace_count = 0
        in_string = False
        escaped = False

        for idx in range(start_idx, len(text)):
            char = text[idx]

            # Handle escaping
            if escaped:
                escaped = False
                continue

            if char == '\\':
                escaped = True
                continue

            # Handle string literals (skip braces inside strings)
            if char == '"':
                in_string = not in_string
                continue

            if in_string:
                continue

            # Handle brace counting
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return idx

        return -1

    def extract_test_class_info(self, content: str) -> Dict[str, str]:
        """Extract namespace, class name, and base class name from test class content"""
        namespace_match = re.search(r'namespace\s+([\w.]+)', content)
        class_match = re.search(r'public\s+class\s+(\w+)(?:\s*:\s*(\w+))?', content)

        return {
            "namespace": namespace_match.group(1) if namespace_match else "",
            "class_name": class_match.group(1) if class_match else "",
            "base_class": class_match.group(2) if class_match else ""
        }

    def extract_test_methods(self, content: str) -> List[Dict]:
        """
        Isolate individual test methods inside the test class.
        
        Returns:
            List of dicts:
                - name: name of the test method
                - attribute: "Fact" or "Theory" (or list of InlineData/Description attributes)
                - signature: e.g. "public void MyTest()" or "public void MyTheory(string age...)"
                - body: content of the method body (excluding outer braces)
                - start_idx: absolute start index in the content
                - end_idx: absolute end index in the content
        """
        methods = []
        # Find all Fact or Theory method decorators
        pattern = re.compile(r'\[(Fact|Theory)\]')
        
        for match in pattern.finditer(content):
            start_idx = match.start()
            
            # Find the opening brace of the method body
            open_brace_match = re.search(r'\{', content[start_idx:])
            if not open_brace_match:
                continue
            
            open_brace_idx = start_idx + open_brace_match.start()
            close_brace_idx = self.find_matching_brace(content, open_brace_idx)
            if close_brace_idx == -1:
                continue
            
            # Extract header/decorator block
            header_block = content[start_idx:open_brace_idx].strip()
            
            # Extract method body
            body = content[open_brace_idx + 1:close_brace_idx]
            
            # Extract method name from the signature
            # Usually public void MethodName() or similar before {
            sig_match = re.search(r'public\s+void\s+(\w+)\s*\(', header_block)
            if not sig_match:
                sig_match = re.search(r'public\s+async\s+Task\s+(\w+)\s*\(', header_block)
                
            method_name = sig_match.group(1) if sig_match else f"TestMethod_{start_idx}"
            
            methods.append({
                "name": method_name,
                "header": header_block,
                "body": body,
                "start_idx": start_idx,
                "end_idx": close_brace_idx + 1
            })

        return methods

    @staticmethod
    def find_class_blocks(content: str) -> List[Dict]:
        """Find all `public class` blocks in the content, at any nesting level"""
        classes = []
        pattern = re.compile(r'public\s+class\s+(\w+)(?:\s*:\s*[\w<>,\s]+)?\s*\{')

        for match in pattern.finditer(content):
            open_brace_idx = content.find('{', match.start())
            if open_brace_idx == -1:
                continue
            close_brace_idx = SkeletonReader.find_matching_brace(content, open_brace_idx)
            if close_brace_idx == -1:
                continue

            classes.append({
                "name": match.group(1),
                "start_idx": match.start(),
                "end_idx": close_brace_idx + 1
            })

        return classes

    def extract_test_classes(self, content: str) -> List[Dict]:
        """
        Returns helper class blocks (e.g. TestFixture, FakeXxx) present in the file,
        excluding the primary test container class (identified as whichever `public class`
        block contains a [Fact] or [Theory] attribute) -- that class must never be
        commented out.
        """
        helper_classes = []
        for c in self.find_class_blocks(content):
            body = content[c["start_idx"]:c["end_idx"]]
            if re.search(r'\[(Fact|Theory)\]', body):
                continue
            helper_classes.append(c)
        return helper_classes

    @staticmethod
    def line_to_offset(content: str, line_num: int) -> int:
        """Convert a 1-based line number into a 0-based character offset into content"""
        if line_num <= 0:
            return 0
        lines = content.splitlines(keepends=True)
        if line_num > len(lines):
            return len(content)
        return sum(len(l) for l in lines[:line_num - 1])

    @staticmethod
    def locate_error(content: str, methods: List[Dict], classes: List[Dict], line_num: int) -> Optional[Dict]:
        """
        Given a 1-based line number (from a compiler error), determine which method or
        class block contains it. Methods are checked first (more specific); falls back to
        the enclosing helper class. Returns None if the line falls in neither (e.g. usings,
        namespace declaration, or the primary test class container).
        """
        offset = SkeletonReader.line_to_offset(content, line_num)

        for m in methods:
            if m["start_idx"] <= offset < m["end_idx"]:
                return {"kind": "method", "name": m["name"], "start_idx": m["start_idx"], "end_idx": m["end_idx"]}

        for c in classes:
            if c["start_idx"] <= offset < c["end_idx"]:
                return {"kind": "class", "name": c["name"], "start_idx": c["start_idx"], "end_idx": c["end_idx"]}

        return None
