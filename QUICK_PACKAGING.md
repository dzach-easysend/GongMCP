# Quick Packaging Reference

**Important:** Run all commands from the project root directory:
```bash
cd /Users/dannyzach/Documents/gong-mcp-server
# or if you're already in the project:
cd /path/to/gong-mcp-server
```

## Build and Verify Package

```bash
# 1. Build the package
pip install build
python -m build

# 2. Verify no secrets are included
./verify_package.sh

# 3. Check package contents manually (optional)
tar -tzf dist/gong_mcp-*.tar.gz | less
```

## What Gets Included

✅ **Included:**
- Source code (`src/gong_mcp/`)
- `README.md`
- `MANIFEST.in`
- `pyproject.toml`
- `.env.example` (template, no secrets)
- `claude_desktop_config.json.example` (template, no secrets)

❌ **Excluded:**
- `.env` files (with actual secrets)
- `claude_desktop_config.json` (with actual secrets)
- `venv/`, `__pycache__/`, test artifacts
- Job data files

## Distribution Options

### Option 1: Share Files Directly
```bash
# Share these files:
dist/gong_mcp-*.whl
dist/gong_mcp-*.tar.gz
README.md
PACKAGING.md
```

### Option 2: Upload to PyPI
```bash
pip install twine
twine upload dist/*
```

### Option 3: Git Repository
```bash
git tag v0.1.0
git push origin v0.1.0
# Users install with: pip install git+https://...
```

## User Installation

Users need to:

1. **Install the package:**
   ```bash
   pip install gong_mcp-*.whl
   ```

2. **Create `.env` file:**
   ```bash
   # Copy template (if included) or create manually
   cat > .env << EOF
   GONG_ACCESS_KEY=their_actual_key
   GONG_ACCESS_KEY_SECRET=their_actual_secret
   ANTHROPIC_API_KEY=their_actual_key
   EOF
   ```

3. **Configure Claude Desktop:**
   - Edit `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Add their credentials in the `env` section

## Pre-Release Checklist

- [ ] No `.env` files in repository
- [ ] No hardcoded secrets in code
- [ ] `.gitignore` excludes all sensitive files
- [ ] `MANIFEST.in` excludes sensitive files
- [ ] Package builds successfully
- [ ] `verify_package.sh` passes
- [ ] Version updated in `pyproject.toml`
- [ ] README updated with installation instructions
