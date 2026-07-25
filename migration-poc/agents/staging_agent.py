"""Staging Agent: Copy components to migrated-output and create feature branches"""
import os
import shutil
import json
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class StagingAgent:
    """Handles component copying and branch creation"""

    def __init__(self, legacy_src_dir: str = "legacy-src", legacy_code_dir: str = "migrated-output"):
        self.legacy_src_dir = legacy_src_dir
        self.legacy_code_dir = legacy_code_dir
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure required directories exist"""
        Path(self.legacy_code_dir).mkdir(parents=True, exist_ok=True)

    def create_feature_branch(self, component_name: str) -> Tuple[bool, str, str]:
        """
        Create feature branch for migration

        Returns:
            Tuple of (success, branch_name, error_message)
        """
        branch_name = self._generate_branch_name(component_name)

        try:
            # Check if branch already exists and append time if it does
            branch_check = subprocess.run(
                ["git", "rev-parse", "--verify", branch_name],
                cwd=os.getcwd(),
                capture_output=True,
                check=False,
                timeout=10
            )

            if branch_check.returncode == 0:
                # Branch exists, append current time to make it unique
                time_suffix = datetime.now().strftime("%H%M%S")
                branch_name = f"{branch_name}-{time_suffix}"

            # Create new branch from main
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print(f"✅ Branch created: {branch_name}")
                return True, branch_name, ""
            else:
                return False, "", f"Failed to create branch: {result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "", "Git operation timed out"
        except Exception as e:
            return False, "", f"Error creating branch: {str(e)}"

    def copy_component(self, component_name: str) -> Tuple[bool, str, Dict]:
        """
        Copy component from legacy-src to migrated-output

        Returns:
            Tuple of (success, error_message, file_manifest)
        """
        src_path = os.path.join(self.legacy_src_dir, component_name)
        dst_path = os.path.join(self.legacy_code_dir, component_name)

        # Validate source exists
        if not os.path.exists(src_path):
            return False, f"Component not found in {src_path}", {}

        if not os.path.isdir(src_path):
            return False, f"Source is not a directory: {src_path}", {}

        # Remove existing destination if it exists
        if os.path.exists(dst_path):
            try:
                shutil.rmtree(dst_path)
            except Exception as e:
                return False, f"Failed to remove existing component: {str(e)}", {}

        try:
            # Copy directory with all contents
            shutil.copytree(src_path, dst_path, symlinks=True, dirs_exist_ok=False)
            print(f"✅ Component copied: {src_path} → {dst_path}")

            # Generate file manifest
            manifest = self._generate_manifest(dst_path)

            return True, "", manifest

        except Exception as e:
            return False, f"Failed to copy component: {str(e)}", {}

    def _generate_branch_name(self, component_name: str) -> str:
        """Generate branch name with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d")
        # Convert to lowercase and replace spaces with hyphens
        sanitized_name = component_name.lower().replace(" ", "-")
        return f"{sanitized_name}-migration-{timestamp}"

    def _generate_manifest(self, directory: str) -> Dict:
        """Generate file manifest with paths and checksums"""
        manifest = {
            "files": [],
            "total_files": 0,
            "total_size_bytes": 0
        }

        for root, dirs, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, directory)

                try:
                    file_size = os.path.getsize(filepath)
                    file_hash = self._calculate_checksum(filepath)

                    manifest["files"].append({
                        "path": rel_path,
                        "size_bytes": file_size,
                        "checksum": file_hash
                    })

                    manifest["total_files"] += 1
                    manifest["total_size_bytes"] += file_size

                except Exception as e:
                    print(f"⚠️  Error processing file {filepath}: {e}")

        return manifest

    def _calculate_checksum(self, filepath: str, algorithm: str = "sha256") -> str:
        """Calculate file checksum"""
        hash_obj = hashlib.new(algorithm)

        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception:
            return ""

    def validate_copy_completeness(self, component_name: str, manifest: Dict) -> Tuple[bool, str]:
        """
        Verify that copy was successful

        Returns:
            Tuple of (is_complete, error_message)
        """
        src_path = os.path.join(self.legacy_src_dir, component_name)
        dst_path = os.path.join(self.legacy_code_dir, component_name)

        try:
            # Count files in source and destination
            src_files = sum(1 for root, dirs, files in os.walk(src_path) for f in files)
            dst_files = sum(1 for root, dirs, files in os.walk(dst_path) for f in files)

            if src_files != dst_files:
                return False, f"File count mismatch: source={src_files}, dest={dst_files}"

            # Verify checksums for a sample of files
            if manifest["files"]:
                for file_info in manifest["files"][:10]:  # Check first 10 files
                    filepath = os.path.join(dst_path, file_info["path"])
                    file_hash = self._calculate_checksum(filepath)

                    if file_hash != file_info["checksum"]:
                        return False, f"Checksum mismatch for {file_info['path']}"

            print(f"✅ Copy verified: {dst_files} files, {manifest['total_size_bytes']} bytes")
            return True, ""

        except Exception as e:
            return False, f"Validation failed: {str(e)}"

    def create_initial_commit(self, component_name: str) -> Tuple[bool, str]:
        """
        Create initial commit with component copy

        Returns:
            Tuple of (success, error_message)
        """
        try:
            component_path = os.path.join(self.legacy_code_dir, component_name)

            # Stage all files
            result = subprocess.run(
                ["git", "add", component_path],
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return False, f"Failed to stage files: {result.stderr}"

            # Create commit
            commit_message = f"Initial copy: {component_name} from legacy-src for migration"
            file_count = sum(1 for root, dirs, files in os.walk(component_path) for f in files)

            result = subprocess.run(
                ["git", "commit", "-m", f"{commit_message}\n\nFiles: {file_count}"],
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print(f"✅ Initial commit created for {component_name}")
                return True, ""
            else:
                return False, f"Commit failed: {result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "Git operation timed out"
        except Exception as e:
            return False, f"Error creating commit: {str(e)}"

    def create_metadata_file(self, component_name: str, manifest: Dict, branch_name: str) -> Tuple[bool, str]:
        """
        Create metadata file documenting the staging operation

        Returns:
            Tuple of (success, error_message)
        """
        try:
            metadata = {
                "component_name": component_name,
                "timestamp": datetime.now().isoformat(),
                "source_path": os.path.join(self.legacy_src_dir, component_name),
                "destination_path": os.path.join(self.legacy_code_dir, component_name),
                "branch_name": branch_name,
                "status": "ready_for_modernization",
                "manifest": manifest
            }

            metadata_path = os.path.join(self.legacy_code_dir, component_name, ".staging_metadata.json")

            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

            print(f"✅ Metadata file created: {metadata_path}")
            return True, ""

        except Exception as e:
            return False, f"Failed to create metadata: {str(e)}"

    def stage_component(self, component_name: str) -> Dict:
        """
        Main staging workflow: branch, copy, validate, commit, metadata

        Returns:
            Dictionary with staging results
        """
        results = {
            "component_name": component_name,
            "timestamp": datetime.now().isoformat(),
            "steps": {}
        }

        print(f"\n[STAGING] Starting staging for {component_name}")
        print("-" * 70)

        # Step 1: Create branch
        success, branch_name, error = self.create_feature_branch(component_name)
        results["steps"]["create_branch"] = {"success": success, "error": error, "branch_name": branch_name}
        if not success:
            print(f"❌ Branch creation failed: {error}")
            return results

        # Step 2: Copy component
        success, error, manifest = self.copy_component(component_name)
        results["steps"]["copy_component"] = {"success": success, "error": error, "file_count": manifest.get("total_files", 0)}
        if not success:
            print(f"❌ Component copy failed: {error}")
            return results

        # Step 3: Validate copy
        success, error = self.validate_copy_completeness(component_name, manifest)
        results["steps"]["validate_copy"] = {"success": success, "error": error}
        if not success:
            print(f"❌ Copy validation failed: {error}")
            return results

        # Step 4: Create initial commit
        success, error = self.create_initial_commit(component_name)
        results["steps"]["create_commit"] = {"success": success, "error": error}
        if not success:
            print(f"⚠️  Commit creation failed (non-fatal): {error}")

        # Step 5: Create metadata
        success, error = self.create_metadata_file(component_name, manifest, branch_name)
        results["steps"]["create_metadata"] = {"success": success, "error": error}
        if not success:
            print(f"⚠️  Metadata creation failed (non-fatal): {error}")

        print("\n✅ Staging complete for {component_name}")
        results["status"] = "success"
        results["branch_name"] = branch_name

        return results


if __name__ == "__main__":
    # Example usage
    agent = StagingAgent()

    # Stage a test component
    # results = agent.stage_component("TestComponent")
    # print(json.dumps(results, indent=2, default=str))
