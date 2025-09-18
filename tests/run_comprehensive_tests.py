#!/usr/bin/env python3
"""
Comprehensive test runner for Gopnik deidentification toolkit.
"""

import sys
import subprocess
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any
import json


class TestRunner:
    """Comprehensive test runner with reporting and CI/CD integration."""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None
    
    def run_unit_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run unit tests with coverage reporting."""
        print("🧪 Running unit tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/",
            "-m", "unit",
            "--cov=src/gopnik",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-report=json:coverage.json",
            "--junit-xml=test-results-unit.xml"
        ]
        
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'duration': 0  # Will be calculated by caller
        }
    
    def run_integration_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run integration tests."""
        print("🔗 Running integration tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/test_integration_workflows.py",
            "-m", "integration",
            "--junit-xml=test-results-integration.xml"
        ]
        
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'duration': 0
        }
    
    def run_performance_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run performance benchmarks."""
        print("⚡ Running performance tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/",
            "-m", "performance",
            "--junit-xml=test-results-performance.xml"
        ]
        
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'duration': 0
        }
    
    def run_security_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run security-focused tests."""
        print("🔒 Running security tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/",
            "-m", "security",
            "--junit-xml=test-results-security.xml"
        ]
        
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'duration': 0
        }
    
    def run_all_tests(self, test_types: List[str] = None, verbose: bool = False) -> Dict[str, Any]:
        """Run all specified test types."""
        if test_types is None:
            test_types = ['unit', 'integration', 'performance', 'security']
        
        self.start_time = time.time()
        
        print("🚀 Starting comprehensive test suite...")
        print(f"📋 Test types: {', '.join(test_types)}")
        print("-" * 60)
        
        results = {}
        
        for test_type in test_types:
            start_time = time.time()
            
            if test_type == 'unit':
                result = self.run_unit_tests(verbose)
            elif test_type == 'integration':
                result = self.run_integration_tests(verbose)
            elif test_type == 'performance':
                result = self.run_performance_tests(verbose)
            elif test_type == 'security':
                result = self.run_security_tests(verbose)
            else:
                print(f"❌ Unknown test type: {test_type}")
                continue
            
            end_time = time.time()
            result['duration'] = end_time - start_time
            results[test_type] = result
            
            # Print immediate result
            if result['exit_code'] == 0:
                print(f"✅ {test_type.capitalize()} tests passed ({result['duration']:.2f}s)")
            else:
                print(f"❌ {test_type.capitalize()} tests failed ({result['duration']:.2f}s)")
                if verbose:
                    print(f"   Error: {result['stderr']}")
        
        self.end_time = time.time()
        self.test_results = results
        
        return results
    
    def generate_coverage_report(self) -> Dict[str, Any]:
        """Generate and parse coverage report."""
        coverage_file = Path("coverage.json")
        if not coverage_file.exists():
            return {'error': 'Coverage report not found'}
        
        try:
            with open(coverage_file) as f:
                coverage_data = json.load(f)
            
            total_statements = coverage_data['totals']['num_statements']
            covered_statements = coverage_data['totals']['covered_lines']
            coverage_percent = coverage_data['totals']['percent_covered']
            
            return {
                'total_statements': total_statements,
                'covered_statements': covered_statements,
                'coverage_percent': coverage_percent,
                'missing_lines': coverage_data['totals']['missing_lines'],
                'files': coverage_data['files']
            }
        except Exception as e:
            return {'error': f'Failed to parse coverage report: {e}'}
    
    def generate_summary_report(self) -> str:
        """Generate a comprehensive summary report."""
        if not self.test_results:
            return "No test results available"
        
        total_duration = self.end_time - self.start_time if self.start_time and self.end_time else 0
        
        report = [
            "=" * 80,
            "🧪 GOPNIK COMPREHENSIVE TEST REPORT",
            "=" * 80,
            f"📅 Execution Time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"⏱️  Total Duration: {total_duration:.2f} seconds",
            "",
            "📊 TEST RESULTS SUMMARY:",
            "-" * 40
        ]
        
        passed_count = 0
        failed_count = 0
        
        for test_type, result in self.test_results.items():
            status = "✅ PASSED" if result['exit_code'] == 0 else "❌ FAILED"
            duration = result['duration']
            
            report.append(f"{test_type.upper():12} | {status} | {duration:6.2f}s")
            
            if result['exit_code'] == 0:
                passed_count += 1
            else:
                failed_count += 1
        
        report.extend([
            "",
            f"📈 OVERALL RESULTS:",
            f"   ✅ Passed: {passed_count}",
            f"   ❌ Failed: {failed_count}",
            f"   📊 Success Rate: {(passed_count / (passed_count + failed_count) * 100):.1f}%"
        ])
        
        # Add coverage information if available
        coverage_info = self.generate_coverage_report()
        if 'error' not in coverage_info:
            report.extend([
                "",
                "📋 CODE COVERAGE:",
                f"   📊 Coverage: {coverage_info['coverage_percent']:.1f}%",
                f"   📝 Statements: {coverage_info['covered_statements']}/{coverage_info['total_statements']}",
                f"   🎯 Target: 80.0%",
                f"   {'✅ Target Met' if coverage_info['coverage_percent'] >= 80 else '❌ Below Target'}"
            ])
        
        # Add recommendations
        report.extend([
            "",
            "💡 RECOMMENDATIONS:",
            "-" * 20
        ])
        
        if failed_count > 0:
            report.append("   🔧 Fix failing tests before deployment")
        
        if 'error' not in coverage_info and coverage_info['coverage_percent'] < 80:
            report.append("   📈 Increase test coverage to meet 80% target")
        
        if all(result['exit_code'] == 0 for result in self.test_results.values()):
            report.append("   🚀 All tests passing - ready for deployment!")
        
        report.extend([
            "",
            "📁 GENERATED FILES:",
            "   📊 htmlcov/index.html - Coverage report",
            "   📋 test-results-*.xml - JUnit test results",
            "   📈 coverage.json - Coverage data",
            "",
            "=" * 80
        ])
        
        return "\n".join(report)
    
    def save_report(self, filename: str = "test-report.txt"):
        """Save the summary report to a file."""
        report = self.generate_summary_report()
        with open(filename, 'w') as f:
            f.write(report)
        print(f"📄 Report saved to {filename}")
    
    def check_quality_gates(self) -> bool:
        """Check if all quality gates pass."""
        # Check if all tests passed
        all_tests_passed = all(
            result['exit_code'] == 0 
            for result in self.test_results.values()
        )
        
        # Check coverage threshold
        coverage_info = self.generate_coverage_report()
        coverage_meets_threshold = (
            'error' not in coverage_info and 
            coverage_info['coverage_percent'] >= 80
        )
        
        return all_tests_passed and coverage_meets_threshold


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="Comprehensive test runner for Gopnik")
    parser.add_argument(
        '--types', 
        nargs='+', 
        choices=['unit', 'integration', 'performance', 'security'],
        default=['unit', 'integration'],
        help='Test types to run'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--report',
        default='test-report.txt',
        help='Report filename'
    )
    parser.add_argument(
        '--ci',
        action='store_true',
        help='CI mode - exit with error code if quality gates fail'
    )
    
    args = parser.parse_args()
    
    # Run tests
    runner = TestRunner()
    results = runner.run_all_tests(args.types, args.verbose)
    
    # Generate and display report
    print("\n" + runner.generate_summary_report())
    
    # Save report
    runner.save_report(args.report)
    
    # Check quality gates for CI
    if args.ci:
        if runner.check_quality_gates():
            print("✅ All quality gates passed")
            sys.exit(0)
        else:
            print("❌ Quality gates failed")
            sys.exit(1)
    
    # Exit with error if any tests failed
    failed_tests = [
        test_type for test_type, result in results.items() 
        if result['exit_code'] != 0
    ]
    
    if failed_tests:
        print(f"❌ Failed test types: {', '.join(failed_tests)}")
        sys.exit(1)
    else:
        print("✅ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()