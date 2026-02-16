# Contributing to PDA Platform

Thank you for your interest in contributing to the PDA Platform! This project provides infrastructure for AI-enabled project delivery.

## Branching Strategy

We use a two-branch workflow:

- **`main`** - Production branch, always deployable
- **`dev`** - Development branch for integrating features

### Branch Protection Rules

**⚠️ IMPORTANT:** While GitHub doesn't enforce these rules automatically on our current plan, all team members must follow these guidelines:

#### Main Branch (`main`)
- **No direct commits** - All changes must come through pull requests
- **Require 1 approving review** - PRs need at least one approval before merging
- **Dismiss stale reviews** - Re-request review when pushing new commits
- **Status checks** - Ensure tests pass before merging
- **Includes administrators** - Admins must also follow these rules

## Development Workflow

### 1. Create a Feature Branch
```bash
# Start from dev branch
git checkout dev
git pull origin dev

# Create your feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes
- Write clear, descriptive commit messages
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass
- Follow existing code style

### 3. Development Setup

#### For pm-data-tools

```bash
cd packages/pm-data-tools
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

#### For agent-task-planning

```bash
cd packages/agent-task-planning
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest
```

#### For pm-mcp-servers

```bash
cd packages/pm-mcp-servers
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### 4. Commit Your Changes
```bash
git add <files>
git commit -m "Brief description of changes"
```

For commits on feature branches, use:
```bash
git config user.name "antnewman"
git config user.email "antjsnewman@outlook.com"
```

### 5. Push and Create Pull Request
```bash
# Push your branch
git push origin feature/your-feature-name

# Create PR via GitHub UI targeting 'dev' branch
```

### 6. Code Review Process
- At least **one approving review** required
- Address all review comments
- Re-request review after making changes
- Ensure all tests and checks pass

### 7. Merging
- Merge feature branches into `dev` after approval
- Merge `dev` into `main` only for production releases

## Pull Request Guidelines

- Provide clear description of changes
- Link related issues if applicable
- Keep PRs focused and reasonably sized
- Ensure all tests pass
- Target `dev` branch (not `main`) for feature PRs

## Feature Branch Naming Convention

Use consistent `feature/` prefix for all feature branches:

✅ **Good:**
- `feature/pm-data-integration`
- `feature/agent-planning-improvements`
- `feature/mcp-server-support`

❌ **Avoid:**
- `updates` (too generic)
- `my-changes` (unclear purpose)
- `testing` (not descriptive)

## Code Style

- **Python** - Follow PEP 8 style guide
- **Type Hints** - Use type annotations
- **Documentation** - Add docstrings for public functions
- **Testing** - Write pytest tests for new features
- **Monorepo** - Changes may affect multiple packages

## Project Structure

```
/packages
  /pm-data-tools         - Project management data tools
  /agent-task-planning   - AI agent task planning library
  /pm-mcp-servers        - MCP servers for project management
/docs                    - Documentation
/examples                - Example implementations
/specs                   - Specifications
```

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

---

**Remember:** Even though GitHub doesn't automatically enforce branch protection, maintaining this workflow ensures code quality and prevents deployment issues.
