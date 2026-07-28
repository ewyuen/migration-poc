"""Staging Agent: Copy components to legacy-code, scoped per migration run"""
import os
import shutil
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class StagingAgent:
    """Handles component copying, scoped by a per-run run_id"""

    def __init__(self, legacy_src_dir: str = "legacy-src", legacy_code_dir: str = "legacy-code"):
        self.legacy_src_dir = legacy_src_dir
        self.legacy_code_dir = legacy_code_dir
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure required directories exist"""
        Path(self.legacy_code_dir).mkdir(parents=True, exist_ok=True)

    def copy_component(self, component_name: str, run_id: str) -> Tuple[bool, str, Dict]:
        """
        Copy component from legacy-src to a run_id-scoped subdirectory of legacy-code

        Returns:
            Tuple of (success, error_message, file_manifest)
        """
        src_path = os.path.join(self.legacy_src_dir, component_name)
        dst_path = os.path.join(self.legacy_code_dir, run_id)

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

    def _generate_run_id(self, component_name: str) -> str:
        """Generate a unique, always-timestamped run_id for this migration run.

        Millisecond precision (not just HH:MM:SS) is needed so two runs
        started in quick succession never collide -- copy_component() removes
        any pre-existing directory at the destination before copying, so a
        collision here would silently overwrite an in-progress run.
        """
        now = datetime.now()
        timestamp = now.strftime("%m%d%y-%H%M%S") + f"-{now.microsecond // 1000:03d}"
        # Convert to lowercase and replace spaces with hyphens
        sanitized_name = component_name.lower().replace(" ", "-")
        return f"{sanitized_name}-{timestamp}"

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

    def validate_copy_completeness(self, component_name: str, run_id: str, manifest: Dict) -> Tuple[bool, str]:
        """
        Verify that copy was successful

        Returns:
            Tuple of (is_complete, error_message)
        """
        src_path = os.path.join(self.legacy_src_dir, component_name)
        dst_path = os.path.join(self.legacy_code_dir, run_id)

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

    def create_metadata_file(self, component_name: str, run_id: str, manifest: Dict) -> Tuple[bool, str]:
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
                "destination_path": os.path.join(self.legacy_code_dir, run_id),
                "run_id": run_id,
                "status": "ready_for_modernization",
                "manifest": manifest
            }

            metadata_path = os.path.join(self.legacy_code_dir, run_id, ".staging_metadata.json")

            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

            print(f"✅ Metadata file created: {metadata_path}")
            return True, ""

        except Exception as e:
            return False, f"Failed to create metadata: {str(e)}"

    def stage_component(self, component_name: str) -> Dict:
        """
        Main staging workflow: generate run_id, copy, validate, metadata

        Returns:
            Dictionary with staging results
        """
        run_id = self._generate_run_id(component_name)

        results = {
            "component_name": component_name,
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "steps": {}
        }

        print(f"\n[STAGING] Starting staging for {component_name} (run_id: {run_id})")
        print("-" * 70)

        # Step 1: Copy component
        success, error, manifest = self.copy_component(component_name, run_id)
        results["steps"]["copy_component"] = {"success": success, "error": error, "file_count": manifest.get("total_files", 0)}
        if not success:
            print(f"❌ Component copy failed: {error}")
            return results

        # Step 2: Validate copy
        success, error = self.validate_copy_completeness(component_name, run_id, manifest)
        results["steps"]["validate_copy"] = {"success": success, "error": error}
        if not success:
            print(f"❌ Copy validation failed: {error}")
            return results

        # Step 3: Create metadata
        success, error = self.create_metadata_file(component_name, run_id, manifest)
        results["steps"]["create_metadata"] = {"success": success, "error": error}
        if not success:
            print(f"⚠️  Metadata creation failed (non-fatal): {error}")

        print(f"\n✅ Staging complete for {component_name}")
        results["status"] = "success"
        results["run_id"] = run_id

        return results


if __name__ == "__main__":
    # Example usage
    agent = StagingAgent()

    # Stage a test component
    # results = agent.stage_component("TestComponent")
    # print(json.dumps(results, indent=2, default=str))
