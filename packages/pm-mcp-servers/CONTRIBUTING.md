# Contributing to PDA-Platform

Thank you for your interest in contributing to pda-platform! This project implements the PDATF White Paper framework for AI-enabled project delivery.

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please:
- Be respectful and constructive
- Focus on the work, not the person
- Welcome newcomers and help them get started

## How to Contribute

### Reporting Issues

1. Check existing issues to avoid duplicates
2. Use the issue template
3. Provide clear reproduction steps
4. Include version information

### Suggesting Features

1. Open a discussion first for major features
2. Explain the use case and benefit
3. Consider how it aligns with PDATF White Paper goals

### Submitting Code

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Run type checking (`mypy src/`)
7. Commit your changes
8. Push to your fork
9. Open a Pull Request

## Development Setup

```bash
# Clone repository
git clone https://github.com/PDA-Task-Force/pda-platform.git
cd pda-platform/packages/pm-mcp-servers

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run type checking
mypy src/
```

## Code Standards

### Python Style

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use meaningful variable names

### Testing

- Write tests for new features
- Maintain >80% test coverage
- Include edge cases
- Test error handling

### Documentation

- Add docstrings to public functions
- Update README for user-facing changes
- Add type hints for clarity
- Include usage examples

## Pull Request Guidelines

### Before Submitting

- [ ] Tests pass locally
- [ ] Type checking passes
- [ ] Documentation updated
- [ ] Changelog updated (if user-facing)
- [ ] Commit messages are clear

### PR Description

Include:
- What problem does this solve?
- How does it work?
- Any breaking changes?
- Related issues

### Review Process

1. Automated checks must pass
2. At least one maintainer review required
3. Address feedback promptly
4. Keep PR scope focused

## Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Testing
- `refactor`: Code refactoring
- `chore`: Maintenance

**Example:**
```
feat: add NISTA validation rule for task dependencies

Implement validation rule to detect circular dependencies
in task networks, addressing NISTA requirement 4.2.3.

Closes #123
```

## Project Structure

```
pm-mcp-servers/
├── src/
│   └── pm_mcp_servers/
│       ├── pm_data/       # Data server
│       ├── pm_validate/   # Validation server
│       └── pm_analyse/    # Analysis server
├── tests/                 # Test suite
├── docs/                  # Documentation
└── examples/              # Usage examples
```

## Testing Guidelines

### Running Tests

```bash
# All tests
pytest

# Specific module
pytest tests/test_pm_data.py

# With coverage
pytest --cov=src --cov-report=html
```

### Writing Tests

```python
def test_load_project():
    """Test project loading functionality."""
    # Arrange
    server = DataServer()
    
    # Act
    result = server.load_project("test.mpp")
    
    # Assert
    assert result.success
    assert result.project_id is not None
```

## Dependency Management

- Minimize dependencies
- Pin versions in setup.py
- Document why each dependency is needed
- Prefer pure Python when possible

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create git tag
4. GitHub Actions handles PyPI publication

## Questions?

- Open a GitHub Discussion
- Email: hello@pdataskforce.com
- Check existing documentation

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in relevant documentation

Thank you for helping improve AI-enabled project delivery!
