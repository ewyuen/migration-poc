"""Service Introspector C#: Regex-based parser to introspect migrated C# code"""
import os
import re
from typing import Dict, List, Tuple, Any, Optional


class ServiceIntrospectorCSharp:
    """Introspects C# source files to discover classes, records, methods, parameters, and constructors"""

    def __init__(self):
        self.classes: Dict[str, Dict[str, Any]] = {}
        self.records: Dict[str, List[Dict[str, str]]] = {}
        self.interfaces: Dict[str, Dict[str, Any]] = {}

    def introspect_directory(self, directory_path: str) -> None:
        """Scan directory and parse all C# files"""
        if not os.path.exists(directory_path):
            return

        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith(".cs") and not file.endswith("Tests.cs"):
                    filepath = os.path.join(root, file)
                    self.introspect_file(filepath)

    def introspect_file(self, filepath: str) -> None:
        """Parse a single C# file and extract symbols"""
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Remove comments to avoid false matches
        content_no_comments = re.sub(r'//.*', '', content)
        content_no_comments = re.sub(r'/\*.*?\*/', '', content_no_comments, flags=re.DOTALL)

        self._parse_records(content_no_comments)
        self._parse_classes(content_no_comments)
        self._parse_interfaces(content_no_comments)

    def _parse_records(self, content: str) -> None:
        """Parse public records like public record AuthRequest(string Email, string Password);"""
        # Match primary constructor style records
        record_pattern = re.compile(r'public\s+record\s+(\w+)\s*\((.*?)\)\s*;', re.DOTALL)
        for match in record_pattern.finditer(content):
            record_name = match.group(1)
            params_str = match.group(2)
            
            params = []
            if params_str.strip():
                # Split parameters, handling commas
                raw_params = params_str.split(',')
                for rp in raw_params:
                    parts = rp.strip().split()
                    if len(parts) >= 2:
                        param_type = parts[0].strip()
                        param_name = parts[1].strip()
                        params.append({"name": param_name, "type": param_type})
            
            self.records[record_name] = params

    def _parse_classes(self, content: str) -> None:
        """Parse classes and extract their constructors and public methods"""
        # Find class declarations
        class_pattern = re.compile(r'public\s+class\s+(\w+)(?:\s*:\s*[\w<>, ]+)?\s*\{', re.DOTALL)
        
        for match in class_pattern.finditer(content):
            class_name = match.group(1)
            start_idx = match.start()
            
            # Find the closing brace of the class to isolate its body
            open_brace_idx = content.find('{', start_idx)
            if open_brace_idx == -1:
                continue
                
            from agents.test_writer.skeleton_reader import SkeletonReader
            close_brace_idx = SkeletonReader.find_matching_brace(content, open_brace_idx)
            if close_brace_idx == -1:
                class_body = content[open_brace_idx + 1:]
            else:
                class_body = content[open_brace_idx + 1:close_brace_idx]

            # Introspect constructor
            constructor_params = self._extract_constructor(class_name, class_body)

            # Introspect public methods
            methods = self._extract_public_methods(class_body)

            self.classes[class_name] = {
                "constructor": constructor_params,
                "methods": methods
            }

    def _parse_interfaces(self, content: str) -> None:
        """Parse public interfaces and extract their method signatures"""
        interface_pattern = re.compile(r'public\s+interface\s+(\w+)(?:\s*:\s*[\w<>, ]+)?\s*\{', re.DOTALL)

        for match in interface_pattern.finditer(content):
            interface_name = match.group(1)
            start_idx = match.start()

            open_brace_idx = content.find('{', start_idx)
            if open_brace_idx == -1:
                continue

            from agents.test_writer.skeleton_reader import SkeletonReader
            close_brace_idx = SkeletonReader.find_matching_brace(content, open_brace_idx)
            if close_brace_idx == -1:
                interface_body = content[open_brace_idx + 1:]
            else:
                interface_body = content[open_brace_idx + 1:close_brace_idx]

            self.interfaces[interface_name] = {
                "methods": self._extract_interface_methods(interface_body)
            }

    def _extract_interface_methods(self, interface_body: str) -> List[Dict[str, Any]]:
        """Extract method signatures declared directly in an interface body (no modifiers, no body)"""
        pattern = re.compile(r'([\w<>\.\[\],\s]+?)\s+(\w+)\s*\((.*?)\)\s*;', re.DOTALL)
        methods = []

        for match in pattern.finditer(interface_body):
            return_type = match.group(1).strip()
            method_name = match.group(2)
            params_str = match.group(3)

            is_async = return_type.startswith("Task") or return_type.startswith("ValueTask")

            params = []
            if params_str.strip():
                raw_params = params_str.split(',')
                for rp in raw_params:
                    parts = rp.strip().split()
                    if len(parts) >= 2:
                        param_type = parts[0].strip()
                        param_name = parts[1].strip()
                        params.append({"name": param_name, "type": param_type})

            methods.append({
                "name": method_name,
                "is_async": is_async,
                "return_type": return_type,
                "parameters": params
            })

        return methods

    def _extract_constructor(self, class_name: str, class_body: str) -> List[Dict[str, str]]:
        """Extract constructor parameters"""
        pattern = re.compile(rf'public\s+{class_name}\s*\((.*?)\)', re.DOTALL)
        match = pattern.search(class_body)
        if not match:
            return []

        params_str = match.group(1)
        params = []
        if params_str.strip():
            # Split parameters
            raw_params = params_str.split(',')
            for rp in raw_params:
                parts = rp.strip().split()
                if len(parts) >= 2:
                    param_type = parts[0].strip()
                    param_name = parts[1].strip()
                    params.append({"name": param_name, "type": param_type})
        return params

    def _extract_public_methods(self, class_body: str) -> List[Dict[str, Any]]:
        """Extract public methods with their parameter types and return types"""
        # Look for public (async)? (return_type) (name) (params)
        pattern = re.compile(r'public\s+(async\s+)?([\w<>\.]+)\s+(\w+)\s*\((.*?)\)', re.DOTALL)
        methods = []

        for match in pattern.finditer(class_body):
            is_async = bool(match.group(1))
            return_type = match.group(2)
            method_name = match.group(3)
            params_str = match.group(4)

            # Skip constructor
            if method_name == "__init__":
                continue

            params = []
            if params_str.strip():
                # Split parameters
                raw_params = params_str.split(',')
                for rp in raw_params:
                    parts = rp.strip().split()
                    if len(parts) >= 2:
                        param_type = parts[0].strip()
                        param_name = parts[1].strip()
                        params.append({"name": param_name, "type": param_type})

            methods.append({
                "name": method_name,
                "is_async": is_async,
                "return_type": return_type,
                "parameters": params
            })

        return methods

    def discover_classes(self) -> List[str]:
        """Returns list of discovered class names"""
        return list(self.classes.keys())

    def discover_methods(self, class_name: str) -> List[Dict[str, Any]]:
        """Returns list of methods for a class"""
        if class_name in self.classes:
            return self.classes[class_name]["methods"]
        return []

    def get_method_signature(self, class_name: str, method_name: str) -> Optional[Dict[str, Any]]:
        """Gets method information for a class and method name"""
        methods = self.discover_methods(class_name)
        for m in methods:
            if m["name"] == method_name:
                return m
        return None

    def find_constructor(self, class_name: str) -> List[Dict[str, str]]:
        """Returns constructor parameters for a class"""
        if class_name in self.classes:
            return self.classes[class_name]["constructor"]
        return []
