"""
Test coverage analysis and enhancement tools.
"""

import pytest
import coverage
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
import json
import ast
import inspect
from unittest.mock import Mock, patch

from tests.test_utils import TestDataGenerator, MockAIEngine, MockDocumentProcessor


class CoverageAnalyzer:
    """Analyze test coverage and identify gaps."""
    
    def __init__(self, source_dir: str = "src/gopnik"):
        self.source_dir = Path(source_dir)
        self.cov = coverage.Coverage()
    
    def run_coverage_analysis(self) -> Dict[str, Any]:
        """Run comprehensive coverage analysis."""
        # Start coverage
        self.cov.start()
        
        # Run tests
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", "--tb=short", "-q"
        ], capture_output=True, text=True)
        
        # Stop coverage
        self.cov.stop()
        self.cov.save()
        
        # Generate report
        report_data = {}
        
        # Get coverage data
        for filename in self.cov.get_data().measured_files():
            if self.source_dir.name in filename:
                rel_path = Path(filename).relative_to(Path.cwd())
                analysis = self.cov.analysis2(filename)
                
                report_data[str(rel_path)] = {
                    'statements': len(analysis[1]),
                    'missing': len(analysis[3]),
                    'excluded': len(analysis[2]),
                    'coverage': (len(analysis[1]) - len(analysis[3])) / len(analysis[1]) * 100 if analysis[1] else 0,
                    'missing_lines': analysis[3]
                }
        
        return report_data
    
    def identify_untested_functions(self) -> Dict[str, List[str]]:
        """Identify functions that lack test coverage."""
        untested = {}
        
        for py_file in self.source_dir.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
                
            try:
                with open(py_file, 'r') as f:
                    tree = ast.parse(f.read())
                
                functions = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if not node.name.startswith("_"):  # Skip private functions
                            functions.append(node.name)
                    elif isinstance(node, ast.ClassDef):
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                                functions.append(f"{node.name}.{item.name}")
                
                if functions:
                    untested[str(py_file.relative_to(Path.cwd()))] = functions
                    
            except Exception as e:
                print(f"Error analyzing {py_file}: {e}")
        
        return untested
    
    def generate_coverage_report(self) -> str:
        """Generate a comprehensive coverage report."""
        analysis = self.run_coverage_analysis()
        untested = self.identify_untested_functions()
        
        report = ["# Test Coverage Analysis Report\n"]
        
        # Overall statistics
        total_statements = sum(data['statements'] for data in analysis.values())
        total_missing = sum(data['missing'] for data in analysis.values())
        overall_coverage = (total_statements - total_missing) / total_statements * 100 if total_statements else 0
        
        report.append(f"## Overall Coverage: {overall_coverage:.2f}%\n")
        report.append(f"- Total Statements: {total_statements}")
        report.append(f"- Missing Coverage: {total_missing}")
        report.append(f"- Coverage Target: 80%\n")
        
        # Per-file breakdown
        report.append("## Per-File Coverage\n")
        for filename, data in sorted(analysis.items(), key=lambda x: x[1]['coverage']):
            status = "✅" if data['coverage'] >= 80 else "❌"
            report.append(f"{status} {filename}: {data['coverage']:.1f}% ({data['statements']} statements, {data['missing']} missing)")
        
        report.append("\n## Files Needing Attention\n")
        for filename, data in analysis.items():
            if data['coverage'] < 80:
                report.append(f"### {filename} ({data['coverage']:.1f}% coverage)")
                if data['missing_lines']:
                    report.append(f"Missing lines: {', '.join(map(str, data['missing_lines']))}")
                report.append("")
        
        return "\n".join(report)


class TestGenerator:
    """Generate missing tests automatically."""
    
    def __init__(self):
        self.test_data = TestDataGenerator()
    
    def generate_unit_test_template(self, module_path: str, class_name: str, 
                                  method_name: str) -> str:
        """Generate a unit test template for a specific method."""
        test_name = f"test_{method_name.lower()}"
        
        template = f'''
def {test_name}(self):
    """Test {class_name}.{method_name} functionality."""
    # Arrange
    # TODO: Set up test data and mocks
    
    # Act
    # TODO: Call the method under test
    
    # Assert
    # TODO: Verify expected behavior
    pytest.fail("Test not implemented")
'''
        return template
    
    def generate_integration_test_template(self, workflow_name: str) -> str:
        """Generate an integration test template for a workflow."""
        template = f'''
@pytest.mark.integration
def test_{workflow_name.lower()}_integration():
    """Test complete {workflow_name} workflow."""
    # Arrange
    with temp_dir() as tmp_dir:
        # TODO: Set up test environment
        
        # Act
        # TODO: Execute complete workflow
        
        # Assert
        # TODO: Verify end-to-end behavior
        pytest.fail("Integration test not implemented")
'''
        return template
    
    def generate_performance_test_template(self, operation_name: str) -> str:
        """Generate a performance test template."""
        template = f'''
@pytest.mark.performance
def test_{operation_name.lower()}_performance():
    """Test {operation_name} performance benchmarks."""
    with PerformanceTimer(max_duration=5.0) as timer:
        # Arrange
        # TODO: Set up performance test data
        
        # Act
        # TODO: Execute operation multiple times
        
        # Assert
        # TODO: Verify performance metrics
        assert timer.duration < 5.0
        pytest.fail("Performance test not implemented")
'''
        return template


@pytest.mark.unit
class TestCoverageAnalyzer:
    """Test the coverage analyzer itself."""
    
    def test_coverage_analyzer_creation(self):
        """Test CoverageAnalyzer creation."""
        analyzer = CoverageAnalyzer()
        assert analyzer.source_dir.name == "gopnik"
        assert analyzer.cov is not None
    
    def test_identify_untested_functions(self):
        """Test identification of untested functions."""
        analyzer = CoverageAnalyzer()
        untested = analyzer.identify_untested_functions()
        
        # Should return a dictionary
        assert isinstance(untested, dict)
        
        # Should have some entries (unless we have 100% coverage)
        # This is expected to fail initially, showing we need more tests
        if untested:
            print("Untested functions found:")
            for file, functions in untested.items():
                print(f"  {file}: {functions}")


@pytest.mark.unit
class TestTestGenerator:
    """Test the test generator functionality."""
    
    def test_generate_unit_test_template(self):
        """Test unit test template generation."""
        generator = TestGenerator()
        template = generator.generate_unit_test_template(
            "src.gopnik.core.processor", "DocumentProcessor", "process_document"
        )
        
        assert "def test_process_document" in template
        assert "DocumentProcessor.process_document" in template
        assert "# Arrange" in template
        assert "# Act" in template
        assert "# Assert" in template
    
    def test_generate_integration_test_template(self):
        """Test integration test template generation."""
        generator = TestGenerator()
        template = generator.generate_integration_test_template("Document Processing")
        
        assert "@pytest.mark.integration" in template
        assert "def test_document_processing_integration" in template
        assert "temp_dir()" in template
    
    def test_generate_performance_test_template(self):
        """Test performance test template generation."""
        generator = TestGenerator()
        template = generator.generate_performance_test_template("Document Analysis")
        
        assert "@pytest.mark.performance" in template
        assert "def test_document_analysis_performance" in template
        assert "PerformanceTimer" in template


# Additional comprehensive tests for core functionality
@pytest.mark.unit
class TestComprehensiveUnitCoverage:
    """Comprehensive unit tests to improve coverage."""
    
    def test_pii_type_enum_completeness(self):
        """Test that all PII types are properly categorized."""
        from src.gopnik.models.pii import PIIType
        
        visual_types = PIIType.visual_types()
        text_types = PIIType.text_types()
        sensitive_types = PIIType.sensitive_types()
        
        # All types should be in either visual or text
        all_categorized = set(visual_types + text_types)
        all_types = set(PIIType)
        assert all_categorized == all_types
        
        # Sensitive types should be a subset of all types
        assert set(sensitive_types).issubset(all_types)
        
        # Visual and text types should not overlap
        assert not set(visual_types).intersection(set(text_types))
    
    def test_bounding_box_edge_cases(self):
        """Test BoundingBox edge cases and error conditions."""
        from src.gopnik.models.pii import BoundingBox
        
        # Test minimum valid box
        bbox = BoundingBox(0, 0, 1, 1)
        assert bbox.width == 1
        assert bbox.height == 1
        assert bbox.area == 1
        
        # Test large coordinates
        bbox = BoundingBox(1000, 2000, 3000, 4000)
        assert bbox.center == (2000.0, 3000.0)
        
        # Test expansion with zero margin
        expanded = bbox.expand(0)
        assert expanded.to_tuple() == bbox.to_tuple()
        
        # Test expansion with large margin
        expanded = bbox.expand(100)
        assert expanded.x1 == 900  # max(0, 1000-100)
        assert expanded.y1 == 1900  # max(0, 2000-100)
        assert expanded.x2 == 3100  # 3000+100
        assert expanded.y2 == 4100  # 4000+100
    
    def test_pii_detection_validation_edge_cases(self):
        """Test PIIDetection validation edge cases."""
        from src.gopnik.models.pii import PIIDetection, PIIType, BoundingBox
        
        bbox = BoundingBox(0, 0, 100, 100)
        
        # Test confidence edge values
        detection = PIIDetection(
            type=PIIType.NAME, bounding_box=bbox, confidence=0.0
        )
        assert detection.confidence == 0.0
        
        detection = PIIDetection(
            type=PIIType.NAME, bounding_box=bbox, confidence=1.0
        )
        assert detection.confidence == 1.0
        
        # Test invalid confidence values
        with pytest.raises(ValueError):
            PIIDetection(
                type=PIIType.NAME, bounding_box=bbox, confidence=-0.1
            )
        
        with pytest.raises(ValueError):
            PIIDetection(
                type=PIIType.NAME, bounding_box=bbox, confidence=1.1
            )
        
        # Test negative page number
        with pytest.raises(ValueError):
            PIIDetection(
                type=PIIType.NAME, bounding_box=bbox, confidence=0.8,
                page_number=-1
            )
    
    def test_processing_result_edge_cases(self):
        """Test ProcessingResult edge cases."""
        from src.gopnik.models.processing import ProcessingResult, ProcessingStatus
        from src.gopnik.models.pii import PIIDetection, PIIType, BoundingBox
        
        # Test with no detections
        result = ProcessingResult(
            document_id="test-123",
            original_filename="test.pdf",
            status=ProcessingStatus.COMPLETED,
            detections=[],
            processing_time=0.0
        )
        
        assert len(result.detections) == 0
        assert result.has_detections() is False
        assert result.get_detection_count() == 0
        assert result.get_detection_types() == []
        
        # Test with multiple detections of same type
        bbox = BoundingBox(0, 0, 100, 100)
        detections = [
            PIIDetection(type=PIIType.NAME, bounding_box=bbox, confidence=0.9),
            PIIDetection(type=PIIType.NAME, bounding_box=bbox, confidence=0.8),
            PIIDetection(type=PIIType.EMAIL, bounding_box=bbox, confidence=0.95)
        ]
        
        result = ProcessingResult(
            document_id="test-456",
            original_filename="test2.pdf",
            status=ProcessingStatus.COMPLETED,
            detections=detections,
            processing_time=2.5
        )
        
        assert result.get_detection_count() == 3
        assert len(result.get_detection_types()) == 2  # NAME and EMAIL
        assert PIIType.NAME in result.get_detection_types()
        assert PIIType.EMAIL in result.get_detection_types()


if __name__ == "__main__":
    # Run coverage analysis
    analyzer = CoverageAnalyzer()
    report = analyzer.generate_coverage_report()
    
    # Save report
    with open("coverage_analysis_report.md", "w") as f:
        f.write(report)
    
    print("Coverage analysis complete. Report saved to coverage_analysis_report.md")