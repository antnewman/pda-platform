# Contributing to PM Data Tools

Thank you for your interest in contributing to PM Data Tools! This document provides guidelines and standards for development.

## Code of Conduct

Be professional, respectful, and constructive in all interactions.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Familiarity with project management concepts (tasks, resources, dependencies)

### Development Setup

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/YourUsername/pm-data-tools.git
   cd pm-data-tools
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Follow these principles:

- **Test-Driven Development (TDD)**: Write tests BEFORE or ALONGSIDE implementation
- **Type hints**: All functions must have type annotations
- **Docstrings**: Google-style docstrings for all public APIs
- **British English**: colour, programme, organisation, optimise, analyse
- **100% coverage**: Pre-commit hooks enforce this

### 3. Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_models/test_task.py

# Check coverage
pytest --cov-report=html
```

### 4. Format and Lint

```bash
# Format code (automatic)
ruff format .

# Check linting
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Type check
mypy src/pm_data_tools
```

### 5. Commit Changes

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```bash
git commit -m "feat: add MSPDI duration parsing"
git commit -m "fix: correct dependency type mapping"
git commit -m "docs: update CLI reference"
git commit -m "test: add roundtrip test for calendars"
```

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Coding Standards

### Python Style

- **Line length**: 88 characters (Black default)
- **Imports**: Organised by stdlib, third-party, local (ruff isort)
- **Naming**:
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_CASE`
- **Type hints**: Mandatory for all function signatures
- **Docstrings**: Google style for all public APIs

Example:

```python
from decimal import Decimal
from typing import Optional


def calculate_variance(
    budgeted: Decimal, actual: Decimal, currency: str = "GBP"
) -> Optional[Decimal]:
    """Calculate budget variance.

    Args:
        budgeted: Budgeted amount.
        actual: Actual amount spent.
        currency: Currency code (default: GBP).

    Returns:
        Variance amount (budgeted - actual), or None if calculation fails.

    Raises:
        ValueError: If currency codes don't match.
    """
    if budgeted.currency != actual.currency:
        raise ValueError(f"Currency mismatch: {budgeted.currency} != {actual.currency}")

    return budgeted - actual
```

### Testing Standards

- **100% coverage required** (enforced by CI)
- **Test file naming**: `test_<module_name>.py`
- **Test class naming**: `Test<ClassName>`
- **Test function naming**: `test_<what_is_being_tested>`

Example:

```python
import pytest
from decimal import Decimal

from pm_data_tools.models import Money


class TestMoney:
    """Tests for Money class."""

    def test_creation_with_default_currency(self) -> None:
        """Test Money creation with default GBP currency."""
        m = Money(Decimal("100"))
        assert m.amount == Decimal("100")
        assert m.currency == "GBP"

    def test_addition_same_currency(self) -> None:
        """Test adding Money with same currency."""
        m1 = Money(Decimal("100"), "GBP")
        m2 = Money(Decimal("50"), "GBP")
        result = m1 + m2

        assert result.amount == Decimal("150")
        assert result.currency == "GBP"

    def test_addition_different_currency_raises(self) -> None:
        """Test that adding Money with different currencies raises ValueError."""
        m1 = Money(Decimal("100"), "GBP")
        m2 = Money(Decimal("50"), "USD")

        with pytest.raises(ValueError, match="Cannot add"):
            m1 + m2
```

### Documentation Standards

- **README.md**: Keep up to date with new features
- **Docstrings**: Google style for all public APIs
- **Type hints**: Serve as inline documentation
- **Examples**: Provide code examples for common use cases

## Architecture

### Three-Layer Design

1. **Models Layer** (`src/pm_data_tools/models/`):
   - Canonical data structures
   - Immutable dataclasses (`@dataclass(frozen=True)`)
   - No business logic, pure data

2. **Schemas Layer** (`src/pm_data_tools/schemas/`):
   - Format-specific parsers (XML → canonical)
   - Format-specific writers (canonical → XML)
   - Mapping logic between formats

3. **Validation Layer** (`src/pm_data_tools/validators/`):
   - Structural validation (references, required fields)
   - Semantic validation (business rules, circular dependencies)

### Adding a New Schema

To add support for a new PM tool:

1. **Create schema directory**:
   ```bash
   mkdir -p src/pm_data_tools/schemas/newtool
   ```

2. **Implement parser** (`src/pm_data_tools/schemas/newtool/parser.py`):
   ```python
   from pm_data_tools.models import Project

   class NewToolParser:
       def parse(self, data: bytes) -> Project:
           """Parse NewTool format to canonical Project."""
           # Implementation
           pass
   ```

3. **Implement writer** (`src/pm_data_tools/schemas/newtool/writer.py`):
   ```python
   from pm_data_tools.models import Project

   class NewToolWriter:
       def write(self, project: Project) -> bytes:
           """Write canonical Project to NewTool format."""
           # Implementation
           pass
   ```

4. **Add tests** (`tests/test_schemas/test_newtool_*.py`):
   - Parser tests
   - Writer tests
   - Roundtrip tests (critical!)

5. **Update CLI** to register new format

## British English Conventions

This library uses British English spelling throughout:

- **colour** (not color)
- **programme** (not program) - for projects
- **organisation** (not organization)
- **optimise** (not optimize)
- **analyse** (not analyze)
- **licence** (noun), **license** (verb)

Dates: DD/MM/YYYY in documentation, ISO 8601 (YYYY-MM-DD) in code

Currency: £ symbol, GBP code

## Git Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation only
- `test/description` - Test improvements
- `refactor/description` - Code refactoring

### Commit Messages

Use Conventional Commits format:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `refactor:` - Code refactoring
- `chore:` - Build/tooling changes
- `perf:` - Performance improvements

### Pull Request Process

1. **Create descriptive PR title**: "feat: Add GMPP schema support"
2. **Fill in PR template**: Describe changes, testing, breaking changes
3. **Ensure CI passes**: All tests pass, 100% coverage maintained
4. **Request review**: At least one reviewer approval required
5. **Address feedback**: Respond to all review comments
6. **Squash and merge**: Keep main branch history clean

## Quality Gates

All pull requests must pass:

- ✅ All tests pass (Python 3.10, 3.11, 3.12)
- ✅ 100% test coverage maintained
- ✅ ruff format (code formatting)
- ✅ ruff check (linting)
- ✅ mypy strict mode (type checking)
- ✅ No security vulnerabilities (Dependabot)

## Getting Help

- **Questions**: Open a [GitHub Discussion](https://github.com/PDATaskForce/pm-data-tools/discussions)
- **Bugs**: Open an [Issue](https://github.com/PDATaskForce/pm-data-tools/issues)
- **Feature requests**: Open an [Issue](https://github.com/PDATaskForce/pm-data-tools/issues) with "enhancement" label

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
