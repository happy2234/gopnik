# Design Document

## Overview

The Gopnik Deidentification Toolkit requires a robust dependency management system that supports multiple deployment scenarios while maintaining clean separation between core functionality and optional features. The current issue stems from core modules importing optional dependencies (like numpy) without proper conditional loading or dependency specification.

This design addresses the dependency management problems and establishes a comprehensive documentation framework to support the existing comprehensive implementation.

## Architecture

### Dependency Management Architecture

The system uses a layered dependency approach:

1. **Core Layer**: Essential dependencies required for basic functionality
2. **Feature Layers**: Optional dependencies grouped by functionality (web, ai, dev)
3. **Conditional Import Layer**: Runtime dependency checking and graceful degradation
4. **Installation Profiles**: Pre-configured dependency sets for common use cases

### Component Structure

```
gopnik/
├── core/                    # Core functionality (minimal dependencies)
│   ├── interfaces.py       # Abstract base classes
│   ├── processor.py        # Document processing orchestrator
│   └── analyzer.py         # Document parsing (conditional AI imports)
├── ai/                     # AI engines (optional numpy/torch dependencies)
│   ├── base_engine.py      # Abstract AI engine interface
│   ├── cv_engine.py        # Computer vision (requires opencv, numpy)
│   ├── nlp_engine.py       # NLP processing (requires transformers)
│   └── hybrid_engine.py    # Combined AI processing
├── interfaces/             # User interfaces
│   ├── cli/               # Command line (core dependencies only)
│   ├── api/               # REST API (requires fastapi)
│   └── web/               # Web interface (requires fastapi, jinja2)
└── utils/                 # Utilities and helpers
    ├── dependency_checker.py  # Runtime dependency validation
    └── conditional_imports.py # Safe optional imports
```

## Components and Interfaces

### Dependency Checker Component

**Purpose**: Validate optional dependencies at runtime and provide clear error messages

**Interface**:
```python
class DependencyChecker:
    def check_ai_dependencies() -> bool
    def check_web_dependencies() -> bool
    def get_missing_dependencies(feature: str) -> List[str]
    def require_dependencies(feature: str) -> None
```

**Implementation Strategy**:
- Use importlib to safely attempt imports
- Maintain feature-to-dependency mapping
- Provide installation guidance in error messages

### Conditional Import Manager

**Purpose**: Handle optional imports gracefully without breaking core functionality

**Interface**:
```python
class ConditionalImports:
    def safe_import(module: str, feature: str) -> Optional[Any]
    def get_fallback_implementation(feature: str) -> Any
    def is_feature_available(feature: str) -> bool
```

**Implementation Strategy**:
- Lazy loading of optional dependencies
- Fallback implementations for missing features
- Clear feature availability reporting

### Installation Profile Manager

**Purpose**: Provide pre-configured installation options for different use cases

**Profiles**:
- `basic`: Core functionality only (CLI, basic redaction)
- `web`: Web interface capabilities
- `ai`: Full AI-powered processing
- `dev`: Development and testing tools
- `all`: Complete installation

## Data Models

### Dependency Configuration Model

```python
@dataclass
class DependencyConfig:
    feature: str
    required_packages: List[str]
    optional_packages: List[str]
    fallback_available: bool
    installation_command: str
```

### Feature Availability Model

```python
@dataclass
class FeatureStatus:
    name: str
    available: bool
    missing_dependencies: List[str]
    installation_guide: str
```

## Error Handling

### Dependency Error Hierarchy

```python
class DependencyError(Exception):
    """Base class for dependency-related errors"""

class MissingDependencyError(DependencyError):
    """Raised when required optional dependency is missing"""
    
class IncompatibleVersionError(DependencyError):
    """Raised when dependency version is incompatible"""
```

### Error Response Strategy

1. **Graceful Degradation**: Core functionality works without optional features
2. **Clear Messaging**: Specific installation instructions for missing dependencies
3. **Feature Detection**: Runtime checks before attempting to use optional features
4. **Installation Guidance**: Contextual help for installing missing components

## Testing Strategy

### Dependency Testing Approach

1. **Matrix Testing**: Test with different dependency combinations
2. **Mock Testing**: Test behavior with missing dependencies
3. **Integration Testing**: Verify optional features work when dependencies are present
4. **Installation Testing**: Validate different installation profiles

### Test Categories

- **Core Tests**: Run with minimal dependencies
- **Feature Tests**: Run with specific optional dependencies
- **Integration Tests**: Full functionality with all dependencies
- **Compatibility Tests**: Version compatibility validation

### Test Implementation

```python
# Example test structure
class TestDependencyManagement:
    def test_core_functionality_without_ai_deps(self):
        """Test basic functionality works without AI dependencies"""
        
    def test_ai_features_with_dependencies(self):
        """Test AI features work when dependencies are available"""
        
    def test_graceful_degradation_missing_deps(self):
        """Test system handles missing dependencies gracefully"""
```

## Implementation Plan Integration

This design addresses the current dependency issues while maintaining compatibility with the existing comprehensive implementation shown in the tasks. The key changes needed are:

1. **Conditional Imports**: Modify core modules to conditionally import optional dependencies
2. **Dependency Validation**: Add runtime checks before using optional features
3. **Error Messaging**: Provide clear guidance when optional dependencies are missing
4. **Installation Profiles**: Update setup configuration to support different installation scenarios
5. **Documentation**: Create comprehensive installation and troubleshooting guides

The design preserves all existing functionality while making the system more robust and user-friendly for different deployment scenarios.