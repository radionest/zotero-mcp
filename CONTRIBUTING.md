# Contributing to Zotero MCP

First off, thank you for considering contributing to Zotero MCP! It's people like you that make this Model Context Protocol (MCP) server for Zotero integration a great tool for the research community.

Following these guidelines helps to communicate that you respect the time of the developers managing and developing this open source project. In return, they should reciprocate that respect in addressing your issue, assessing changes, and helping you finalize your pull requests.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Git Workflow](#git-workflow)
- [Commit Message Conventions](#commit-message-conventions)
- [Code Style and Standards](#code-style-and-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Code Review Guidelines](#code-review-guidelines)
- [Issue Reporting Guidelines](#issue-reporting-guidelines)
- [Community Guidelines](#community-guidelines)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

We love contributions from everyone. Here are ways you can contribute:

- **Report bugs**: If you find a bug, please open an issue with a clear description
- **Suggest enhancements**: Have an idea to improve Zotero MCP? We'd love to hear it
- **Write documentation**: Help us improve our docs or add examples
- **Submit code**: Fix bugs, add features, or improve existing code
- **Help others**: Answer questions in issues or discussions

### First Time Contributors

Unsure where to begin? Look for issues labeled `good first issue` or `help wanted`. These are great starting points for new contributors.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- A Zotero account with API access
- (Optional) uv for fast Python package management

### Setting Up Your Development Environment

1. **Fork the repository**
   ```bash
   # Click the 'Fork' button on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/zotero-mcp.git
   cd zotero-mcp
   ```

2. **Set up the upstream remote**
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/zotero-mcp.git
   ```

3. **Install dependencies**

   Using uv (recommended):
   ```bash
   uv pip install -e ".[dev]"
   ```

   Using pip:
   ```bash
   pip install -e ".[dev]"
   ```

4. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

5. **Configure your Zotero credentials**
   ```bash
   python -m zotero_mcp.setup_helper
   ```

## Git Workflow

We use a feature branch workflow to maintain code quality and project stability.

### Branching Strategy

- **`main`**: The stable branch. Always deployable.
- **`dev`**: The development branch for integrating features (if used).
- **Feature branches**: Created from `main` for new features or fixes.

### Creating a Feature Branch

```bash
# Update your local main branch
git checkout main
git pull upstream main

# Create and switch to a new branch
git checkout -b feature/your-feature-name
```

### Branch Naming Conventions

- `feature/` - New features (e.g., `feature/add-collection-search`)
- `fix/` - Bug fixes (e.g., `fix/rate-limit-handling`)
- `docs/` - Documentation changes (e.g., `docs/improve-setup-guide`)
- `refactor/` - Code refactoring (e.g., `refactor/simplify-api-client`)
- `test/` - Test additions or fixes (e.g., `test/add-semantic-search-tests`)

## Commit Message Conventions

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. This leads to more readable messages that are easy to follow when looking through the project history.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **chore**: Changes to the build process or auxiliary tools

### Examples

```bash
# Feature
git commit -m "feat(semantic-search): add hybrid embedding support"

# Bug fix
git commit -m "fix(cli): resolve rate limiting in batch operations"

# Documentation
git commit -m "docs(setup): clarify Smithery installation steps"

# With body
git commit -m "feat(server): add WebDAV attachment support

- Implement WebDAV client for direct attachment access
- Add configuration for WebDAV credentials
- Include fallback to API when WebDAV unavailable

Closes #123"
```

## Code Style and Standards

### Python Code Style

We use [Black](https://github.com/psf/black) for code formatting and follow PEP 8 guidelines.

- **Formatting**: Run `black src/` before committing
- **Type hints**: Use type hints for function parameters and return values
- **Docstrings**: Use Google-style docstrings for functions and classes
- **Async/await**: Use async patterns for I/O operations when appropriate

### Example

```python
from typing import List, Optional

async def search_items(
    query: str,
    collection_id: Optional[str] = None,
    limit: int = 10
) -> List[dict]:
    """Search for items in the Zotero library.
    
    Args:
        query: The search query string
        collection_id: Optional collection ID to search within
        limit: Maximum number of results to return
        
    Returns:
        List of matching Zotero items
        
    Raises:
        ZoteroAPIError: If the API request fails
    """
    # Implementation here
    pass
```

### Import Organization

1. Standard library imports
2. Third-party imports
3. Local application imports

Each group separated by a blank line, sorted alphabetically within groups.

## Testing Requirements

All contributions should include appropriate tests.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=zotero_mcp

# Run specific test file
pytest tests/test_semantic_search.py
```

### Writing Tests

- Place tests in the `tests/` directory
- Mirror the source code structure
- Use descriptive test names
- Include both positive and negative test cases
- Mock external API calls

### Test Checklist

- [ ] Unit tests for new functions/methods
- [ ] Integration tests for API interactions
- [ ] Edge cases are covered
- [ ] Tests pass locally
- [ ] No decrease in code coverage

## Pull Request Process

1. **Ensure your branch is up to date**
   ```bash
   git checkout main
   git pull upstream main
   git checkout your-branch
   git rebase main
   ```

2. **Run quality checks**
   ```bash
   # Format code
   black src/
   
   # Run tests
   pytest
   
   # Check types (if applicable)
   mypy src/
   ```

3. **Push your branch**
   ```bash
   git push origin your-branch
   ```

4. **Create a Pull Request**
   - Use a clear, descriptive title
   - Reference any related issues
   - Fill out the PR template completely
   - Add screenshots for UI changes

### PR Template

```markdown
## Summary
Brief description of changes

## Changes
- List specific modifications
- Reference related issues

## Testing
- [ ] Tested with Python 3.10+
- [ ] Verified semantic search functionality
- [ ] Checked CLI commands
- [ ] All tests pass

## Installation methods verified
- [ ] uv
- [ ] pip
- [ ] pipx
- [ ] conda (if applicable)
```

## Code Review Guidelines

### For Authors

- Keep PRs small and focused
- Respond to feedback constructively
- Update your PR based on review comments
- Be patient - reviewers are volunteers

### For Reviewers

- Be constructive and kind
- Explain your reasoning
- Suggest specific improvements
- Approve when the PR meets standards

### Review Checklist

- [ ] Code follows project style guidelines
- [ ] Tests are included and pass
- [ ] Documentation is updated if needed
- [ ] No unnecessary files are included
- [ ] Commit history is clean
- [ ] PR description is complete

## Issue Reporting Guidelines

### Before Creating an Issue

- Check existing issues (including closed ones)
- Search the documentation
- Try the latest version

### Creating a Bug Report

Include:
- Clear, descriptive title
- Steps to reproduce
- Expected behavior
- Actual behavior
- System information (OS, Python version, etc.)
- Error messages/logs
- Minimal reproducible example

### Feature Requests

Include:
- Use case description
- Proposed solution
- Alternative solutions considered
- Additional context

### Issue Templates

Use the provided issue templates when available. They help ensure all necessary information is included.

## Community Guidelines

### Be Respectful

- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully
- Focus on what is best for the community

### Be Collaborative

- Help others when you can
- Share knowledge and experiences
- Acknowledge others' contributions
- Ask for help when needed

### Be Professional

- Stay on topic in discussions
- Avoid personal attacks
- Respect maintainer decisions
- Follow through on commitments

## Getting Help

- **Documentation**: Check our [README](README.md) and docs
- **Issues**: Search existing issues or create a new one
- **Discussions**: Join our GitHub Discussions for questions
- **Contact**: Reach out to maintainers for sensitive matters

## Recognition

Contributors are recognized in our [AUTHORS](AUTHORS.md) file. We appreciate every contribution, no matter how small!

## Final Notes

Remember, contributing to open source should be fun and rewarding. If you're stuck or unsure about anything, don't hesitate to ask for help. We're here to support each other and build something great together.

Thank you for contributing to Zotero MCP! 🎉