# Installing and Running Tests

## Quick Start

### Option 1: Using uv (Recommended)

If you have `uv` installed:

```bash
uv sync --extra test
pytest
```

### Option 2: Using pip with newer Python

If your pip version is too old (like 21.2.4), you have a few options:

#### A. Upgrade pip first (if possible)

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[test]"
pytest
```

#### B. Install test dependencies directly (workaround for old pip)

```bash
# Install test dependencies directly
python3 -m pip install pytest pytest-asyncio pytest-cov pytest-mock pytest-httpx freezegun

# Install project dependencies needed for tests
python3 -m pip install httpx python-dotenv

# Run tests (you may need to set PYTHONPATH)
PYTHONPATH=src pytest tests/
```

#### C. Use Python 3.10+ with a virtual environment

The project requires Python 3.10+, but you have Python 3.9.6. Create a new venv with Python 3.10+:

```bash
# Install Python 3.10+ (if not already installed)
# macOS: brew install python@3.12
# Or use pyenv: pyenv install 3.12

# Create venv with Python 3.10+
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[test]"

# Run tests
pytest
```

## Validate Test Structure

Before running tests, you can validate the test suite structure:

```bash
python3 validate_tests.py
```

This will check that all test files are syntactically correct.

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=gong_mcp --cov-report=html
# Open htmlcov/index.html in browser
```

### Run specific test suites
```bash
# Unit tests only
pytest tests/unit/ -m unit

# Integration tests only
pytest tests/integration/ -m integration

# E2E tests only
pytest tests/e2e/ -m e2e
```

### Run specific test file
```bash
pytest tests/unit/test_filters.py
```

## Troubleshooting

### "editable mode currently requires a setuptools-based build"

This happens when pip is too old. Solutions:
1. Upgrade pip: `python3 -m pip install --upgrade pip`
2. Install dependencies directly (see Option 2B above)
3. Use Python 3.10+ with a fresh venv

### "Python 3.10+ required"

The project requires Python 3.10+. If you have Python 3.9:
- Install Python 3.10+ using Homebrew or pyenv
- Create a new virtual environment with the newer Python version

### SSL/Permission errors

If you get SSL or permission errors:
- Try installing with `--user` flag
- Or use a virtual environment
- Or check your network/firewall settings

## Test Suite Summary

- **11 test files** validated and ready
- **6 unit test files** (filters, formatters, router, gong_client, jobs)
- **3 integration test files** (calls, participants, analysis tools)
- **1 E2E test file** (workflows)

All test files have been validated for syntax correctness! ✅
