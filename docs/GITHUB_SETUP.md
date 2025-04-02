# GitHub Setup Guide for Crawl4AI

This document provides instructions for setting up and working with the Crawl4AI GitHub repository.

## Initial Repository Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/crawl4ai.git
   cd crawl4ai
   ```

2. Set up your Git identity:
   ```bash
   git config user.name "Your Name"
   git config user.email "your.email@example.com"
   ```

3. Initialize the project using the provided script:
   ```bash
   cd scripts
   ./init_github.bat
   ```

4. Create the repository on GitHub:
   - Go to [GitHub](https://github.com/new)
   - Create a new repository named "crawl4ai"
   - Do not initialize it with README, .gitignore, or license

5. Push your code to GitHub:
   ```bash
   git remote add origin https://github.com/yourusername/crawl4ai.git
   git branch -M main
   git push -u origin main
   ```

## Development Workflow

### Branching

We use a simplified Git flow workflow:

1. `main` - Production-ready code
2. `dev` - Development branch
3. Feature branches - Created from `dev` for new features

To create a new feature branch:
```bash
git checkout dev
git pull
git checkout -b feature/your-feature-name
```

### Committing Changes

Follow the commit message format:
```
feat(component): Brief description of change

Longer description explaining the rationale, if needed.
```

Example commit types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code refactoring
- `test`: Tests
- `chore`: Build tasks, configs, etc.

### Creating Pull Requests

1. Push your feature branch:
   ```bash
   git push -u origin feature/your-feature-name
   ```

2. Go to GitHub and create a Pull Request to the `dev` branch
3. Fill out the PR template with all required information
4. Request a review from team members
5. Address any feedback from code review
6. Once approved, merge the PR

## Working with Issues

1. Check the existing issues before creating a new one
2. Use the provided templates for bug reports and feature requests
3. Label issues appropriately
4. Assign issues to team members when appropriate
5. Reference issues in commit messages and PRs using `#issue-number`

## Releases

1. Merge `dev` into `main` when ready for a release:
   ```bash
   git checkout main
   git pull
   git merge dev
   git push
   ```

2. Create a new release on GitHub:
   - Go to Releases in the repository
   - Click "Create a new release"
   - Tag version: v0.1.0 (follow semantic versioning)
   - Title: Version 0.1.0
   - Description: List major changes and improvements
   - Select "main" branch

## Best Practices

1. Keep commits focused on a single change
2. Write descriptive commit messages
3. Pull before pushing to avoid conflicts
4. Update documentation when adding or changing features
5. Write tests for new functionality
6. Regularly merge `main` into `dev` to stay up-to-date 