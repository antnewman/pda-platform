# Contributing to Agent Task Planning

Thank you for your interest in contributing! This project is developed by [Members of the PDA Task Force](https://PDA Platform.co.uk) and maintained by the [PDA Task Force](https://github.com/PDATaskForce).

## Code of Conduct

This project follows our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

## How to Contribute

### Reporting Bugs

Before submitting a bug report:
1. Check existing issues to avoid duplicates
2. Use the bug report template
3. Include reproduction steps, expected behaviour, and actual behaviour
4. Include your Python version and OS

### Suggesting Features

1. Check existing issues and discussions first
2. Use the feature request template
3. Explain the use case and why existing features don't suffice

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add or update tests as needed
5. Ensure all tests pass (`pytest`)
6. Run linting (`ruff check .`)
7. Run type checking (`mypy src`)
8. Commit with clear messages
9. Push and open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/agent-task-planning.git
cd agent-task-planning

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev,all]"

# Install pre-commit hooks (optional)
pre-commit install

# Run tests
pytest

# Run linting
ruff check .

# Run type checking
mypy src
```

### Code Style

- We use `ruff` for linting and formatting
- Type hints are required for all public functions
- Docstrings follow Google style
- British English in documentation (organisation, behaviour, etc.)
- No em dashes in prose, use commas or restructure

### Testing

- All new features require tests
- Maintain or improve code coverage
- Use `pytest-asyncio` for async tests
- Mock external API calls

### Documentation

- Update relevant docs for user-facing changes
- Include docstrings for public APIs
- Add examples for new features

## Architecture Decisions

Major architectural changes should be discussed in an issue first. We value:

1. **Simplicity over cleverness**
2. **Explicit over implicit**
3. **Provider-agnostic design**
4. **Production-readiness** (guardrails, observability, error handling)

## Maintainers

This repository is maintained by the [PDA Task Force](https://github.com/PDATaskForce) community. For questions about the original design and implementation, contact [Members of the PDA Task Force](https://PDA Platform.co.uk).

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for general questions
- Contact the PDA Task Force for maintainer enquiries
