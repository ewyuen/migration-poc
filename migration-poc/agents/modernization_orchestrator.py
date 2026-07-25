"""Modernization Orchestrator Agent: Coordinates self-healing modernization loop"""
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
from agents.code_compiler import compile_modernized_code, format_errors_for_feedback

class ModernizationOrchestrator:
    """Coordinates the modernizer and code compiler in a self-healing loop"""

    def __init__(self, base_output_dir: str = "migrated-output", config: Optional[Dict] = None):
        """
        Initialize the ModernizationOrchestrator.

        Args:
            base_output_dir: Base directory for output (default: "migrated-output")
            config: Configuration dictionary with optional max_attempts
        """
        self.base_output_dir = base_output_dir
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.max_attempts = self.config.get("max_attempts", 3)

    def execute(self, component_name: str, modernizer_func, legacy_code: str, extraction_results: str, exploration_results: str) -> Dict:
        """
        Executes the self-healing modernization loop.

        Args:
            component_name: Name of the component being modernized
            modernizer_func: Function that generates modernized code (callable)
            legacy_code: The legacy code to modernize
            extraction_results: Results from extraction stage
            exploration_results: Results from exploration stage

        Returns:
            Dictionary with keys:
            - status: "success" or "failed"
            - modernized_code: The final modernized code (empty if failed)
            - errors: List of compilation errors from final attempt (empty if success)
            - attempts: Number of attempts made
            - compiled: Boolean indicating if code compiled
        """
        attempt = 1
        errors = []
        modernized_code = ""

        self.logger.info(f"🔄 Modernization Orchestrator: Starting self-healing loop for {component_name}")
        self.logger.info(f"🔄 Modernization Orchestrator: Max attempts = {self.max_attempts}")

        while attempt <= self.max_attempts:
            self.logger.info(f"🔄 Modernization Orchestrator: Attempt {attempt} of {self.max_attempts}")

            # 1. Generate (or refine) modernized code
            self.logger.info(f"✍️ Modernization Orchestrator: Generating modernized code (attempt {attempt})...")

            if attempt == 1:
                # First attempt: fresh generation
                modernized_code = modernizer_func(legacy_code, extraction_results, exploration_results)
            else:
                # Subsequent attempts: pass errors back to modernizer for refinement
                feedback = format_errors_for_feedback(errors)
                attempt_context = {
                    "attempt": attempt,
                    "max_attempts": self.max_attempts,
                    "previous_errors": feedback
                }
                modernized_code = modernizer_func(
                    legacy_code,
                    extraction_results,
                    exploration_results,
                    feedback_errors=errors,
                    attempt_context=attempt_context
                )

            # 2. Compile and check
            self.logger.info(f"🔨 Modernization Orchestrator: Compiling modernized code...")
            compiled, errors = compile_modernized_code(modernized_code, component_name, self.base_output_dir)

            if compiled:
                self.logger.info(f"✅ Modernization Orchestrator: Code compiled successfully on attempt {attempt}!")
                self._save_modernized_code(component_name, modernized_code)
                return {
                    "status": "success",
                    "modernized_code": modernized_code,
                    "errors": [],
                    "attempts": attempt,
                    "compiled": True
                }

            # Compilation failed, extract errors for next iteration
            self.logger.warning(f"⚠️ Modernization Orchestrator: Compilation failed on attempt {attempt}.")
            self.logger.warning(f"   Errors: {[e['message'] for e in errors[:3]]}")
            attempt += 1

        # Max attempts exhausted
        self.logger.error(f"❌ Modernization Orchestrator: Code failed to compile after {self.max_attempts} attempts.")
        self._save_modernized_code(component_name, modernized_code)
        return {
            "status": "failed",
            "modernized_code": modernized_code,
            "errors": errors,
            "attempts": self.max_attempts,
            "compiled": False
        }

    def _save_modernized_code(self, component_name: str, modernized_code: str) -> None:
        """Save the modernized code to disk (final version only)"""
        try:
            output_dir = os.path.join(self.base_output_dir, component_name)
            os.makedirs(output_dir, exist_ok=True)

            # Save as ModernizedCode.cs
            output_file = os.path.join(output_dir, "ModernizedCode.cs")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(modernized_code)

            self.logger.info(f"💾 Modernization Orchestrator: Saved modernized code to {output_file}")
        except Exception as e:
            self.logger.error(f"❌ Modernization Orchestrator: Failed to save modernized code: {e}")
