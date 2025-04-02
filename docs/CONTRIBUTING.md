# Contributing Guidelines

Last Updated: **April 2, 2024**

## Overview

This document outlines the process for contributing to the Crawl4AI project. It includes guidelines for code style, pull requests, testing requirements, and documentation standards.

## Getting Started

1. **Fork the Repository**: Start by forking the repository to your own GitHub account.

2. **Clone the Repository**: Clone your fork to your local machine.
   ```bash
   git clone https://github.com/yourusername/Crawl4AI.git
   cd Crawl4AI
   ```

3. **Set Up Development Environment**:
   - Install Python 3.8 or higher
   - Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
   - Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a Branch**: Create a branch for your feature or bugfix.
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Code Style Guidelines

### Python Code Style

1. **Follow PEP 8**: Adhere to [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code.

2. **Use Type Hints**: Include type hints for function parameters and return values.
   ```python
   def process_url(url: str) -> dict:
       # Function implementation
       return result
   ```

3. **Docstrings**: Include docstrings for all modules, classes, and functions.
   ```python
   def extract_content(html: str, selectors: list) -> str:
       """
       Extract content from HTML using specified selectors.
       
       Args:
           html: HTML content to parse
           selectors: List of CSS selectors to use for extraction
           
       Returns:
           Extracted text content
           
       Raises:
           ValueError: If no content is found
       """
       # Function implementation
   ```

4. **Maximum Line Length**: Keep lines under 100 characters.

5. **Imports**: Organize imports into standard library, third-party, and local application imports with a blank line between each group.

### JavaScript/TypeScript Code Style

1. **Follow ESLint Configuration**: Ensure your code passes the project's ESLint rules.

2. **Use TypeScript**: Write new frontend code in TypeScript rather than JavaScript.

3. **React Components**: Use functional components with hooks instead of class components.

4. **Props and State Types**: Define explicit types for component props and state.
   ```typescript
   interface CrawlerFormProps {
     onSubmit: (urls: string[]) => void;
     isLoading: boolean;
   }
   
   const CrawlerForm: React.FC<CrawlerFormProps> = ({ onSubmit, isLoading }) => {
     // Component implementation
   };
   ```

## Commit Guidelines

1. **Atomic Commits**: Make each commit a logical unit of change.

2. **Commit Messages**: Use clear and descriptive commit messages.
   - First line should be a summary (50 chars or less)
   - Followed by a blank line
   - Followed by a detailed description if necessary

3. **Reference Issues**: Reference relevant issue numbers in commit messages.
   ```
   Fix content extraction for JavaScript-rendered pages
   
   Adds support for waiting until JavaScript loads before extracting content.
   This fixes issue #42 where JavaScript-rendered content was not being captured.
   ```

## Pull Request Process

1. **Create a Pull Request**: Push your branch to your fork and create a pull request to the main repository.

2. **Pull Request Description**: Include a clear description of the changes, the problem they solve, and any relevant issue numbers.

3. **Code Review**: Address any feedback from code reviews promptly.

4. **Continuous Integration**: Ensure all CI checks pass before requesting a review.

5. **Approval**: Pull requests require approval from at least one maintainer before merging.

## Testing Guidelines

1. **Write Tests**: Include tests for all new features and bug fixes.

2. **Test Coverage**: Aim for at least 80% test coverage for new code.

3. **Running Tests**:
   ```bash
   python -m pytest tests/
   ```

4. **Test Types**:
   - **Unit Tests**: Test individual functions and classes in isolation
   - **Integration Tests**: Test interactions between components
   - **End-to-End Tests**: Test complete workflows

## Documentation Guidelines

1. **Update Documentation**: Update relevant documentation for any changes.
   - Update API documentation for any changes to the API
   - Update user guides for any changes to user-facing features
   - Update architectural documentation for any structural changes

2. **Documentation Format**: Use Markdown for documentation.

3. **Documentation Location**: Place documentation in the appropriate location:
   - Code-level documentation as docstrings
   - API documentation in `docs/API.md`
   - User guides in `docs/Setup_and_Usage.md`
   - Technical details in appropriate technical documents

## Feature Development Process

1. **Discuss First**: For significant changes, open an issue for discussion before implementation.

2. **Design Document**: For complex features, create a design document outlining the approach.

3. **Prototype**: Consider creating a prototype for experimental features.

4. **Implement**: Implement the feature following the guidelines above.

5. **Test**: Write comprehensive tests for the feature.

6. **Document**: Update documentation to cover the new feature.

7. **Submit**: Create a pull request with the changes.

## Bug Fix Process

1. **Reproduce**: Ensure you can reproduce the bug consistently.

2. **Write Test**: Write a test that fails due to the bug.

3. **Fix Bug**: Implement the fix so the test passes.

4. **Regression Tests**: Ensure existing tests still pass.

5. **Document**: Update documentation if necessary.

6. **Submit**: Create a pull request with the fix.

## Code Review Guidelines

When reviewing code, consider the following:

1. **Functionality**: Does the code work as intended?

2. **Code Quality**: Is the code well-written, clear, and maintainable?

3. **Performance**: Are there any performance concerns?

4. **Security**: Are there any security vulnerabilities?

5. **Tests**: Are there appropriate tests for the changes?

6. **Documentation**: Is the documentation updated appropriately?

7. **Consistency**: Does the code follow project conventions?

## Release Process

1. **Version Bump**: Update version numbers in relevant files.

2. **Changelog**: Update the changelog with a summary of changes.

3. **Release Notes**: Create detailed release notes for significant releases.

4. **Tag Release**: Tag the release in Git.
   ```bash
   git tag -a v1.2.0 -m "Version 1.2.0"
   git push origin v1.2.0
   ```

5. **Publish**: Publish the release on GitHub.

## Community Guidelines

1. **Be Respectful**: Treat all contributors with respect.

2. **Be Patient**: Not everyone has the same level of expertise.

3. **Be Constructive**: Provide constructive feedback.

4. **Be Collaborative**: Work together to improve the project.

## License

By contributing to this project, you agree that your contributions will be licensed under the project's license. 