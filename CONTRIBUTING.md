# Contributing to Home Assistant Galaxie Integration

Thank you for your interest in contributing to the Home Assistant Galaxie integration!

## Development Setup

1. Fork the repository
2. Clone your fork locally
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install development dependencies:
   ```bash
   pip install aiohttp pytest black isort flake8 pylint
   ```

## Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Follow Home Assistant's [development guidelines](https://developers.home-assistant.io/docs/development_index/)

## Testing

Run the test suite:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest --cov=custom_components.galaxie tests/
```

## Submitting Changes

1. Create a feature branch from `main`
2. Make your changes
3. Add tests for new functionality
4. Update documentation if needed
5. Run the test suite
6. Submit a pull request

## Pull Request Guidelines

- Provide a clear description of the changes
- Include tests for new functionality
- Update documentation if needed
- Ensure all tests pass
- Follow the existing code style

## Reporting Issues

When reporting issues, please include:
- Home Assistant version
- Integration version
- Python version
- Error logs
- Steps to reproduce
- Expected vs actual behavior 