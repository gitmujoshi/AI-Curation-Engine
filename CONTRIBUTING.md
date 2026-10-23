# Contributing to Perimeter

Thank you for your interest in contributing to Perimeter! This document provides guidelines and instructions for contributing.

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please be respectful and professional in all interactions.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)

### Suggesting Features

Feature requests are welcome! Please:
- Check if the feature already exists
- Provide clear use cases
- Explain why this would benefit users

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/perimeter.git
   cd perimeter
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Write clean, documented code
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation as needed

4. **Run tests**
   ```bash
   pytest tests/
   ```

5. **Run linting**
   ```bash
   black src/
   ruff check src/
   mypy src/
   ```

6. **Commit your changes**
   ```bash
   git commit -m "feat: add new feature"
   ```
   
   Use conventional commit messages:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `test:` for test changes
   - `refactor:` for code refactoring

7. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Open a Pull Request**
   - Provide clear description of changes
   - Reference any related issues
   - Ensure CI passes

## Development Setup

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Redis
- PostgreSQL

### Local Setup

```bash
# Clone repository
git clone https://github.com/perimeter-ai/gateway.git
cd perimeter

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
pip install -e ".[dev]"

# Start services
docker-compose up -d

# Run tests
pytest tests/
```

## Code Style

We use:
- **Black** for code formatting (line length: 100)
- **Ruff** for linting
- **MyPy** for type checking
- **pytest** for testing

### Pre-commit Hooks

Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

## Testing

### Unit Tests

```bash
pytest tests/unit/ -v
```

### Integration Tests

```bash
pytest tests/integration/ -v
```

### Coverage

```bash
pytest tests/ --cov=src --cov-report=html
```

## Documentation

- Keep docstrings up to date
- Update README.md for user-facing changes
- Update docs/ for architecture changes
- Add examples for new features

## Security

If you discover a security vulnerability, please email security@perimeter.ai instead of opening a public issue.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Feel free to open an issue or reach out to the maintainers.

Thank you for contributing to Perimeter! 🔒
