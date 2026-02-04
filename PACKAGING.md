# Packaging Guide for Gong MCP Server

This guide explains how to package and distribute the Gong MCP Server without exposing any secret keys or sensitive information.

**Important:** All packaging commands should be run from the project root directory (where `pyproject.toml` is located).

## Security Checklist

Before packaging, ensure:

- ✅ No `.env` files are included
- ✅ No actual API keys in any configuration files
- ✅ `claude_desktop_config.json` is excluded (use `.example` version only)
- ✅ All secrets are loaded from environment variables only
- ✅ `.gitignore` properly excludes sensitive files

## Required Files

### 1. Environment Variables Template

Create a `.env.example` file (template, no actual secrets):

```bash
# Gong MCP Server Environment Variables
# Copy this file to .env and fill in your actual credentials
# DO NOT commit .env to version control

# Gong API Credentials
GONG_ACCESS_KEY=your_gong_access_key_here
GONG_ACCESS_KEY_SECRET=your_gong_access_key_secret_here

# Anthropic API Key (optional, for batch analysis)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Token threshold for smart routing (default: 150000)
# DIRECT_TOKEN_THRESHOLD=150000
```

**Note:** The `.env.example` file should be included in the package, but the actual `.env` file should NEVER be included.

## Building the Package

### Option 1: Build with `hatchling` (Recommended)

```bash
# Install build tools
pip install build

# Build the package
python -m build

# This creates:
# - dist/gong_mcp-0.1.0.tar.gz (source distribution)
# - dist/gong_mcp-0.1.0-py3-none-any.whl (wheel distribution)
```

### Option 2: Build with `uv`

```bash
# Build the package
uv build

# Output will be in dist/
```

### Option 3: Build with `setuptools`

```bash
pip install setuptools wheel
python setup.py sdist bdist_wheel
```

## Verifying Package Contents

Before distributing, verify that no secrets are included:

```bash
# Extract and inspect the source distribution
tar -tzf dist/gong_mcp-*.tar.gz | grep -E '\.env|secret|key|config\.json'

# Should return nothing (or only .env.example and *.example files)

# Check the wheel contents
unzip -l dist/gong_mcp-*.whl | grep -E '\.env|secret|key|config\.json'

# Should return nothing (or only .env.example and *.example files)
```

## Distribution Methods

### 1. PyPI (Public Distribution)

For public distribution on PyPI:

```bash
# Install twine
pip install twine

# Upload to PyPI (test first with TestPyPI)
twine upload --repository testpypi dist/*

# If successful, upload to real PyPI
twine upload dist/*
```

**Important:** Only upload if you want this to be publicly available. The package itself doesn't contain secrets, but users will need to configure their own credentials.

### 2. Private PyPI Server

For internal/private distribution:

```bash
# Upload to your private PyPI server
twine upload --repository-url https://your-private-pypi.com/upload dist/*
```

### 3. Direct File Distribution (Recommended for Non-Technical Users)

Share these **4 files together**:

```bash
# Required files to share:
# - dist/gong_mcp-0.1.0-py3-none-any.whl (the package)
# - install.bat (Windows installer script)
# - install.sh (Mac/Linux installer script)
# - INSTALL.md (simple installation instructions)
```

**Easiest way:** Put all 4 files in a folder, zip it, and share the zip file.

Users just need to:
1. Extract the files (if shared as zip)
2. Double-click `install.bat` (Windows) or `install.sh` (Mac/Linux)
3. Follow `INSTALL.md` for configuration

See [HOW_TO_SHARE.md](HOW_TO_SHARE.md) for simple distribution instructions.

### 4. Git Repository Distribution

If distributing via Git:

```bash
# Ensure .gitignore is up to date
git add .gitignore MANIFEST.in pyproject.toml

# Tag the release
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0

# Users can install with:
pip install git+https://github.com/yourusername/gong-mcp-server.git@v0.1.0
```

## Installation Instructions for Users

Provide these instructions to users who receive your package:

### 1. Install the Package

```bash
# From PyPI
pip install gong-mcp

# From wheel file
pip install gong_mcp-0.1.0-py3-none-any.whl

# From source distribution
pip install gong_mcp-0.1.0.tar.gz

# From Git
pip install git+https://github.com/yourusername/gong-mcp-server.git
```

### 2. Configure Environment Variables

Users must set up their own credentials. They have two options:

#### Option A: Using `.env` file

```bash
# Copy the example file
cp .env.example .env

# Edit .env with their actual credentials
# GONG_ACCESS_KEY=their_actual_key
# GONG_ACCESS_KEY_SECRET=their_actual_secret
# ANTHROPIC_API_KEY=their_actual_key
```

#### Option B: Using environment variables directly

```bash
export GONG_ACCESS_KEY="their_actual_key"
export GONG_ACCESS_KEY_SECRET="their_actual_secret"
export ANTHROPIC_API_KEY="their_actual_key"
```

### 3. Configure Claude Desktop

Users should create their own `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gong": {
      "command": "gong-mcp",
      "env": {
        "GONG_ACCESS_KEY": "their_actual_key",
        "GONG_ACCESS_KEY_SECRET": "their_actual_secret",
        "ANTHROPIC_API_KEY": "their_actual_key"
      }
    }
  }
}
```

**Important:** Users should NEVER commit their `claude_desktop_config.json` with real credentials to version control.

## Pre-Packaging Checklist

Before building and distributing:

- [ ] Verify `.gitignore` excludes all `.env*` files
- [ ] Verify `MANIFEST.in` excludes sensitive files
- [ ] Check that no hardcoded secrets exist in source code
- [ ] Ensure `claude_desktop_config.json.example` has placeholder values only
- [ ] Create `.env.example` with placeholder values
- [ ] Test that the package builds successfully
- [ ] Verify package contents don't include secrets
- [ ] Update version number in `pyproject.toml` if needed
- [ ] Update `README.md` with installation instructions

## Version Management

Update the version in `pyproject.toml`:

```toml
[project]
version = "0.1.0"  # Update this for each release
```

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality in a backwards compatible manner
- **PATCH** version for backwards compatible bug fixes

## Troubleshooting

### Package includes sensitive files

If you find secrets in the built package:

1. Check `MANIFEST.in` - ensure exclusions are correct
2. Check `.gitignore` - ensure sensitive files are ignored
3. Clean and rebuild:
   ```bash
   rm -rf dist/ build/ *.egg-info
   python -m build
   ```

### Users can't find `.env.example`

The `.env.example` file should be included via `MANIFEST.in`. If it's missing:

1. Verify `MANIFEST.in` includes: `include .env.example`
2. Rebuild the package
3. Alternatively, provide it separately in documentation

## Best Practices

1. **Never commit secrets** - Always use environment variables
2. **Use example files** - Provide `.example` versions of config files
3. **Document clearly** - Make it obvious where users should put their credentials
4. **Test installation** - Test the package installation in a clean environment
5. **Version control** - Tag releases in Git for traceability
6. **Security audit** - Regularly review what files are included in packages
