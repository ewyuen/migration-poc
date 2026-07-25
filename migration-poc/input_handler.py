"""User Input Handler: Accept and validate migration requests"""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class MigrationRequest:
    """Represents a user migration request"""

    def __init__(self, component_name: str, filters: Optional[Dict] = None):
        self.component_name = component_name
        self.filters = filters or {}
        self.timestamp = datetime.now().isoformat()
        self.request_id = f"{component_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    def to_dict(self) -> Dict:
        return {
            "request_id": self.request_id,
            "component_name": self.component_name,
            "filters": self.filters,
            "timestamp": self.timestamp
        }


class InputHandler:
    """Handles user input validation and parsing"""

    def __init__(self, legacy_src_dir: str = "legacy-src", audit_dir: str = "migration-poc/audit"):
        self.legacy_src_dir = legacy_src_dir
        self.audit_dir = audit_dir
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure required directories exist"""
        Path(self.audit_dir).mkdir(parents=True, exist_ok=True)

    def validate_component_name(self, component_name: str) -> Tuple[bool, str]:
        """
        Validate component name parameter

        Args:
            component_name: Name of component to migrate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not component_name:
            return False, "Component name cannot be empty"

        if len(component_name) > 255:
            return False, "Component name too long (max 255 characters)"

        # Allow alphanumeric, hyphens, underscores
        if not all(c.isalnum() or c in '-_.' for c in component_name):
            return False, "Component name contains invalid characters. Use alphanumeric, hyphens, underscores, or dots."

        return True, ""

    def validate_filters(self, filters: Optional[Dict]) -> Tuple[bool, str]:
        """
        Validate optional filters parameter

        Args:
            filters: Optional dictionary of filters (domain, dependency, size, etc.)

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not filters:
            return True, ""

        if not isinstance(filters, dict):
            return False, "Filters must be a dictionary"

        valid_filter_keys = {"domain", "dependency", "size", "language", "namespace"}
        for key in filters.keys():
            if key not in valid_filter_keys:
                return False, f"Unknown filter: {key}. Valid filters: {valid_filter_keys}"

        return True, ""

    def validate_legacy_src_exists(self) -> Tuple[bool, str]:
        """
        Validate that legacy-src directory exists

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not os.path.exists(self.legacy_src_dir):
            return False, f"Legacy source directory '{self.legacy_src_dir}' not found"

        if not os.path.isdir(self.legacy_src_dir):
            return False, f"'{self.legacy_src_dir}' is not a directory"

        return True, ""

    def log_request(self, request: MigrationRequest) -> str:
        """
        Log migration request for audit trail

        Args:
            request: MigrationRequest object

        Returns:
            Path to the log file
        """
        log_file = os.path.join(self.audit_dir, "migration_requests.jsonl")

        log_entry = {
            **request.to_dict(),
            "status": "received"
        }

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

        return log_file

    def parse_cli_args(self, component_name: str, filters: Optional[str] = None) -> Tuple[Optional[MigrationRequest], str]:
        """
        Parse CLI arguments and create migration request

        Args:
            component_name: Component to migrate
            filters: Optional JSON string with filters

        Returns:
            Tuple of (MigrationRequest or None, error_message)
        """
        # Validate legacy-src exists
        is_valid, error = self.validate_legacy_src_exists()
        if not is_valid:
            return None, error

        # Validate component name
        is_valid, error = self.validate_component_name(component_name)
        if not is_valid:
            return None, error

        # Parse filters if provided
        parsed_filters = {}
        if filters:
            try:
                parsed_filters = json.loads(filters)
            except json.JSONDecodeError as e:
                return None, f"Invalid filters JSON: {e}"

        # Validate filters
        is_valid, error = self.validate_filters(parsed_filters)
        if not is_valid:
            return None, error

        # Create request
        request = MigrationRequest(component_name, parsed_filters)

        # Log request
        self.log_request(request)

        return request, ""

    def parse_interactive_input(self) -> Tuple[Optional[MigrationRequest], str]:
        """
        Parse interactive user input from command line

        Returns:
            Tuple of (MigrationRequest or None, error_message)
        """
        print("\n" + "="*70)
        print("COMPONENT MIGRATION WORKFLOW")
        print("="*70)

        # Get component name
        while True:
            component_name = input("\nEnter component name to migrate: ").strip()
            is_valid, error = self.validate_component_name(component_name)
            if is_valid:
                break
            print(f"❌ Invalid: {error}")

        # Ask about filters
        filters_str = input("Enter optional filters as JSON (press Enter to skip): ").strip()

        if filters_str:
            try:
                parsed_filters = json.loads(filters_str)
            except json.JSONDecodeError as e:
                return None, f"Invalid filters JSON: {e}"
        else:
            parsed_filters = {}

        # Validate filters
        is_valid, error = self.validate_filters(parsed_filters)
        if not is_valid:
            return None, error

        # Create and log request
        request = MigrationRequest(component_name, parsed_filters)
        self.log_request(request)

        return request, ""

    def get_available_components(self) -> List[Dict]:
        """
        Get list of available components in legacy-src

        Returns:
            List of component info dictionaries
        """
        components = []

        if not os.path.exists(self.legacy_src_dir):
            return components

        for item in os.listdir(self.legacy_src_dir):
            path = os.path.join(self.legacy_src_dir, item)

            # Check if it's a .NET project (has .csproj or .sln)
            if os.path.isdir(path):
                has_csproj = any(f.endswith('.csproj') for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
                has_sln = any(f.endswith('.sln') for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))

                if has_csproj or has_sln:
                    # Count files
                    file_count = sum(1 for root, dirs, files in os.walk(path) for f in files)

                    components.append({
                        "name": item,
                        "path": path,
                        "type": ".sln" if has_sln else ".csproj",
                        "file_count": file_count
                    })

        return sorted(components, key=lambda x: x["name"])

    def list_available_components(self) -> None:
        """Print available components to user"""
        components = self.get_available_components()

        if not components:
            print("❌ No components found in legacy-src/")
            return

        print("\n📦 Available Components in legacy-src/:")
        print("-" * 70)
        for i, comp in enumerate(components, 1):
            print(f"{i:2}. {comp['name']:<40} ({comp['type']:<8}) {comp['file_count']:>3} files")
        print("-" * 70)


if __name__ == "__main__":
    # Example usage
    handler = InputHandler()

    # Example 1: Parse CLI arguments
    request, error = handler.parse_cli_args("MyComponent", '{"domain": "Authentication"}')
    if error:
        print(f"Error: {error}")
    else:
        print(f"Request created: {request.to_dict()}")

    # Example 2: List available components
    handler.list_available_components()
