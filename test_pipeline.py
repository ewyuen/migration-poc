#!/usr/bin/env python
"""Quick end-to-end pipeline test"""
import sys
import os

# Set working directory
os.chdir(os.path.join(os.path.dirname(__file__), 'migration-poc'))
sys.path.insert(0, os.getcwd())

from orchestrator_v3 import OrchestratorV3
from input_handler import MigrationRequest

orchestrator = OrchestratorV3()
request = MigrationRequest(component_name='TestService')
result = orchestrator.orchestrate_migration(request)

print(f"\n{'='*60}")
print(f"Pipeline Stage: {result.get('current_stage')}")
print(f"Status: {result.get('status')}")
print(f"Error: {result.get('error')}")
print(f"{'='*60}\n")

# Check if tests directory was created
run_id = result.get('run_id')
if run_id:
    tests_dir = f'migrated-output/{run_id}/tests'
    if os.path.exists(tests_dir):
        print(f"✅ Tests directory created: {tests_dir}")
        print(f"   Files: {os.listdir(tests_dir)}")
    else:
        print(f"❌ Tests directory NOT found: {tests_dir}")
else:
    print("❌ No run_id - pipeline failed early")
