# Running Tests - Quick Guide

## Prerequisites

Make sure you have:
1. **Python 3.10+** (the project requires Python 3.10 or later)
2. **Virtual environment activated** (if using one)

## Quick Start

### 1. Activate Virtual Environment

```bash
# If using the project's venv
source venv/bin/activate

# Verify Python version
python --version  # Should be 3.10+
```

### 2. Install Dependencies (if not already done)

```bash
pip install -e ".[test]"
```

### 3. Run All Tests

```bash
pytest
```

## Common Test Commands

### Run all tests with verbose output
```bash
pytest -v
```

### Run specific test file
```bash
pytest tests/unit/test_filters.py
```

### Run specific test
```bash
pytest tests/unit/test_filters.py::TestFilterCallsByEmails::test_filter_by_exact_email
```

### Run tests by marker
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# E2E tests only
pytest -m e2e
```

### Run with coverage report
```bash
pytest --cov=gong_mcp --cov-report=html
# Then open htmlcov/index.html in your browser
```

### Run with coverage (terminal output)
```bash
pytest --cov=gong_mcp --cov-report=term-missing
```

### Stop on first failure
```bash
pytest -x
```

### Show local variables on failure
```bash
pytest -l
```

### Run tests in parallel (if pytest-xdist installed)
```bash
pytest -n auto
```

## Test Structure

```
tests/
├── unit/              # Unit tests (isolated components)
├── integration/       # Integration tests (component interactions)
└── e2e/              # End-to-end tests (full workflows)
```

## Expected Results

When all tests pass, you should see:
```
============================= 139 passed in 0.52s ==============================
```

## Troubleshooting

### "Python 3.10+ required"
- Make sure you're using Python 3.10 or later
- Check: `python --version`
- If needed, create a new venv with Python 3.10+:
  ```bash
  python3.11 -m venv venv
  source venv/bin/activate
  pip install -e ".[test]"
  ```

### "Module not found" errors
- Make sure dependencies are installed: `pip install -e ".[test]"`
- Make sure virtual environment is activated

### Tests failing with HTTP errors
- Tests use mocks - they shouldn't make real API calls
- If you see 401/403 errors, the mocks aren't working properly
- Check that `pytest-httpx` is installed

## Quick Reference

| Command | Description |
|---------|-------------|
| `pytest` | Run all tests |
| `pytest -v` | Verbose output |
| `pytest -m unit` | Unit tests only |
| `pytest --cov=gong_mcp` | With coverage |
| `pytest -x` | Stop on first failure |
| `pytest tests/unit/` | Run unit tests directory |
