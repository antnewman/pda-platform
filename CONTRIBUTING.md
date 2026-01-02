# Contributing to PDA Platform

Thank you for your interest in contributing to the PDA Platform! This project provides infrastructure for AI-enabled project delivery.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/pda-platform.git`
3. Create a branch: `git checkout -b feature/your-feature-name`

## Development Setup

### For pm-data-tools

```bash
cd packages/pm-data-tools
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

### For agent-task-planning

```bash
cd packages/agent-task-planning
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest
```

### For pm-mcp-servers

```bash
cd packages/pm-mcp-servers
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

## Making Changes

1. Write clear, descriptive commit messages
2. Add tests for new functionality
3. Update documentation as needed
4. Ensure all tests pass
5. Follow existing code style

## Submitting Changes

1. Push to your fork
2. Open a Pull Request
3. Describe your changes clearly
4. Link any related issues

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help maintain a welcoming community

## Questions?

Open an issue on GitHub if you need help or have questions.

## Attribution

All contributions will be attributed to "Members of the PDA Task Force" as per the project license.

## Acknowledgments

This work supports the NISTA Programme and Project Data Standard trial.
