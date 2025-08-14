#!/usr/bin/env python3
"""
Deploy the City Brain Urban Planning Simulator to Modal.
This script handles the deployment process and provides deployment status.
"""

import subprocess
import sys
import time
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{description}...")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed")
        print(f"Error code: {e.returncode}")
        if e.stdout:
            print(f"Stdout: {e.stdout.strip()}")
        if e.stderr:
            print(f"Stderr: {e.stderr.strip()}")
        return False

def check_modal_status():
    """Check if Modal is properly configured."""
    print("Checking Modal configuration...")
    
    try:
        result = subprocess.run("modal token current", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Modal token found: {result.stdout.strip()}")
            return True
        else:
            print("✗ No Modal token found")
            print("Please run 'modal token new' to authenticate")
            return False
    except Exception as e:
        print(f"✗ Error checking Modal status: {e}")
        return False

def deploy_app():
    """Deploy the Modal app."""
    print("\nDeploying City Brain Urban Planning Simulator to Modal...")
    
    # Check if we're in the right directory
    project_root = Path.cwd()
    modal_app_path = project_root / "citybrain" / "modal_app.py"
    
    if not modal_app_path.exists():
        print(f"✗ Modal app not found at {modal_app_path}")
        print("Please run this script from the project root directory")
        return False
    
    # Deploy the app
    deploy_command = f"modal deploy {modal_app_path}"
    if not run_command(deploy_command, "Deploying Modal app"):
        return False
    
    print("\n✓ Modal app deployed successfully!")
    return True

def test_deployment():
    """Test the deployed app with a simple query."""
    print("\nTesting deployed app...")
    
    test_command = 'modal run citybrain/modal_app.py::get_scenario_insights --query "If we pedestrianize Broadway from 14th to 34th in NYC, what zoning amendments would be required?"'
    
    if not run_command(test_command, "Testing deployed app"):
        print("Note: This is expected to fail if you don't have the required environment variables set")
        print("The app is still deployed and ready for use with proper configuration")
        return True
    
    return True

def main():
    """Main deployment function."""
    print("City Brain Urban Planning Simulator - Modal Deployment")
    print("=" * 60)
    
    # Check Modal configuration
    if not check_modal_status():
        print("\nPlease configure Modal first:")
        print("1. Install Modal: pip install modal")
        print("2. Authenticate: modal token new")
        print("3. Run this script again")
        return
    
    # Deploy the app
    if not deploy_app():
        print("\n✗ Deployment failed")
        return
    
    # Test the deployment
    test_deployment()
    
    print("\n" + "=" * 60)
    print("✓ Deployment completed successfully!")
    print("\nYour City Brain Urban Planning Simulator is now deployed on Modal!")
    print("\nNext steps:")
    print("1. Set up environment variables in Modal dashboard")
    print("2. Test with: modal run citybrain/modal_app.py::get_scenario_insights")
    print("3. Build a frontend to consume the API")
    print("4. Scale up resources as needed")
    
    print("\nModal app endpoints:")
    print("• Main function: citybrain/modal_app.py::get_scenario_insights")
    print("• Data ingestion: citybrain/modal_app.py::ingest_all_data")
    print("• LLM processing: citybrain/modal_app.py::process_scenario_with_llm")

if __name__ == "__main__":
    main() 