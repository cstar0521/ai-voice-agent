#!/usr/bin/env python3
"""
End-to-End Test Runner for AI Voice Loan Agent

Executes comprehensive E2E testing including:
- End-to-end scenarios
- Load testing  
- User acceptance testing

Usage:
    python run_e2e_tests.py [--test-type TYPE] [--verbose]
    
Test Types:
    - scenarios: End-to-end scenarios only
    - load: Load testing only
    - uat: User acceptance testing only
    - all: All tests (default)
"""
import argparse
import asyncio
import sys
import time
from pathlib import Path
import subprocess
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def run_pytest_command(test_file: str, verbose: bool = False) -> dict:
    """Run pytest command and capture results."""
    cmd = ["python", "-m", "pytest", test_file, "-v"]
    if verbose:
        cmd.append("-s")
    
    # Add JSON report if plugin is available
    try:
        import pytest_json_report
        report_file = f"test_report_{Path(test_file).stem}.json"
        cmd.extend(["--json-report", f"--json-report-file={report_file}"])
    except ImportError:
        report_file = None
    
    print(f"\nRunning: {' '.join(cmd)}")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
        end_time = time.time()
        
        # Parse JSON report if available
        test_results = {}
        if report_file:
            report_path = Path(__file__).parent / report_file
            if report_path.exists():
                try:
                    with open(report_path) as f:
                        test_results = json.load(f)
                except Exception as e:
                    print(f"Warning: Could not parse test report: {e}")
        
        return {
            "success": result.returncode == 0,
            "duration": end_time - start_time,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "test_results": test_results
        }
    
    except Exception as e:
        return {
            "success": False,
            "duration": time.time() - start_time,
            "error": str(e),
            "stdout": "",
            "stderr": str(e),
            "return_code": -1,
            "test_results": {}
        }

def print_test_summary(results: dict):
    """Print formatted test summary."""
    print("\n" + "=" * 80)
    print("TEST EXECUTION SUMMARY")
    print("=" * 80)
    
    total_duration = 0
    total_tests = 0
    total_passed = 0
    total_failed = 0
    
    for test_type, result in results.items():
        print(f"\n{test_type.upper()} TESTS:")
        print("-" * 40)
        
        if result["success"]:
            print(f"✅ Status: PASSED")
        else:
            print(f"❌ Status: FAILED")
        
        print(f"⏱️  Duration: {result['duration']:.2f}s")
        
        # Extract test counts from JSON report
        test_results = result.get("test_results", {})
        if "summary" in test_results:
            summary = test_results["summary"]
            passed = summary.get("passed", 0)
            failed = summary.get("failed", 0)
            total = summary.get("total", 0)
            
            print(f"📊 Tests: {total} total, {passed} passed, {failed} failed")
            
            total_tests += total
            total_passed += passed
            total_failed += failed
        
        total_duration += result["duration"]
        
        # Print any errors
        if not result["success"] and result.get("stderr"):
            print(f"❗ Error: {result['stderr'][:200]}...")
    
    print("\n" + "=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)
    print(f"📊 Total Tests: {total_tests}")
    print(f"✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_failed}")
    print(f"⏱️  Total Duration: {total_duration:.2f}s")
    
    if total_failed == 0:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️  {total_failed} TESTS FAILED")
    
    return total_failed == 0

def run_end_to_end_scenarios(verbose: bool = False) -> dict:
    """Run end-to-end scenario tests."""
    print("\n🔄 Running End-to-End Scenario Tests...")
    return run_pytest_command("tests/test_e2e_scenarios.py", verbose)

def run_load_tests(verbose: bool = False) -> dict:
    """Run load testing scenarios."""
    print("\n🔄 Running Load Tests...")
    return run_pytest_command("tests/test_load_testing.py", verbose)

def run_user_acceptance_tests(verbose: bool = False) -> dict:
    """Run user acceptance tests."""
    print("\n🔄 Running User Acceptance Tests...")
    return run_pytest_command("tests/test_user_acceptance.py", verbose)

def check_prerequisites():
    """Check if all prerequisites are met for E2E testing."""
    print("🔍 Checking prerequisites...")
    
    # Check if pytest is installed
    try:
        import pytest
        print("✅ pytest is available")
    except ImportError:
        print("❌ pytest not found. Install with: pip install pytest")
        return False
    
    # Check if pytest-json-report is installed
    try:
        subprocess.run(["python", "-m", "pytest", "--help"], 
                      capture_output=True, check=True)
        print("✅ pytest is working")
    except subprocess.CalledProcessError:
        print("❌ pytest not working properly")
        return False
    
    # Check if test files exist
    test_files = [
        "tests/test_e2e_scenarios.py",
        "tests/test_load_testing.py", 
        "tests/test_user_acceptance.py"
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"✅ {test_file} found")
        else:
            print(f"❌ {test_file} not found")
            return False
    
    return True

def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run E2E tests for AI Voice Loan Agent")
    parser.add_argument("--test-type", choices=["scenarios", "load", "uat", "all"], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Verbose output")
    
    args = parser.parse_args()
    
    print("🚀 AI Voice Loan Agent - End-to-End Test Runner")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Exiting.")
        sys.exit(1)
    
    results = {}
    
    try:
        if args.test_type in ["scenarios", "all"]:
            results["scenarios"] = run_end_to_end_scenarios(args.verbose)
        
        if args.test_type in ["load", "all"]:
            results["load"] = run_load_tests(args.verbose)
        
        if args.test_type in ["uat", "all"]:
            results["uat"] = run_user_acceptance_tests(args.verbose)
        
        # Print summary
        all_passed = print_test_summary(results)
        
        # Exit with appropriate code
        sys.exit(0 if all_passed else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()