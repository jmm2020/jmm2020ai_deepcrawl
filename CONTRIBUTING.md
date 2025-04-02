# Contributing to Crawl4AI

Thank you for your interest in contributing to Crawl4AI! This document provides guidelines and workflows for contributing to this project.

## Development Workflow

### Branching Strategy

We use a simplified Git Flow workflow:

1. `main` - Production-ready code
2. `dev` - Development branch, stable but with newer features
3. Feature branches - Created from `dev` for new features or bug fixes

### Pull Request Process

1. Fork the repository and create a feature branch from `dev`
2. Implement your changes with appropriate tests
3. Ensure all tests pass before submitting a PR
4. Submit a PR to the `dev` branch
5. Address any feedback from code reviews

## Code Standards

### Python Code

- Follow PEP 8 style guidelines
- Use type hints for function signatures
- Document functions with Google-style docstrings
- Format code with `black` 
- Keep functions focused on a single responsibility
- Maximum line length: 100 characters

### Testing

- Every new feature should include unit tests
- Tests should be in the `tests/` directory 
- Follow the existing test structure
- Include at least one happy path test and one edge case test

### Commit Messages

Write clear commit messages using the following format:

```
feat(component): Brief description of change

Longer description explaining the rationale, if needed.
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding tests
- `chore`: Updating build tasks, package manager configs, etc.

## Setting Up Local Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/crawl4ai.git
   cd crawl4ai
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

4. Run tests to ensure everything is working:
   ```bash
   python -m unittest discover tests
   ```

## Documentation

- Update documentation when adding or modifying features
- Keep the README.md up-to-date with any dependency or config changes
- Follow Markdown best practices for documentation files

## Questions and Discussions

For questions or discussions about development, please:
- Open a Discussion on GitHub
- Use the issue tracker for specific bugs or features

Thank you for contributing to Crawl4AI! 