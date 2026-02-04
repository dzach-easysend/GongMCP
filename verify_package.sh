#!/bin/bash
# Verification script to ensure no secrets are included in the package

set -e

echo "🔍 Verifying package contents for secrets..."

# Check if package exists
if [ ! -d "dist" ] || [ -z "$(ls -A dist/*.tar.gz 2>/dev/null)" ]; then
    echo "❌ No package found. Build the package first with: python -m build"
    exit 1
fi

# Find the most recent package
PACKAGE=$(ls -t dist/*.tar.gz | head -1)
echo "📦 Checking package: $PACKAGE"

# Check for sensitive files
echo ""
echo "Checking for sensitive files..."

SENSITIVE_FILES=$(tar -tzf "$PACKAGE" 2>/dev/null | grep -E '\.env$|\.env\.[^e]|secret|\.key$|\.pem$|config\.json$' | grep -v '\.example' || true)

if [ -n "$SENSITIVE_FILES" ]; then
    echo "❌ WARNING: Found potentially sensitive files in package:"
    echo "$SENSITIVE_FILES"
    echo ""
    echo "⚠️  Review these files and ensure they don't contain secrets!"
    exit 1
else
    echo "✅ No sensitive files found (excluding .example files)"
fi

# Check for .env.example (should be included)
echo ""
echo "Checking for .env.example template..."
if tar -tzf "$PACKAGE" 2>/dev/null | grep -q '\.env\.example'; then
    echo "✅ .env.example template found"
else
    echo "⚠️  .env.example not found (users will need this for configuration)"
fi

# Check for claude_desktop_config.json.example
echo ""
echo "Checking for claude_desktop_config.json.example..."
if tar -tzf "$PACKAGE" 2>/dev/null | grep -q 'claude_desktop_config\.json\.example'; then
    echo "✅ claude_desktop_config.json.example found"
else
    echo "⚠️  claude_desktop_config.json.example not found"
fi

# Check for README
echo ""
echo "Checking for documentation..."
if tar -tzf "$PACKAGE" 2>/dev/null | grep -q 'README\.md'; then
    echo "✅ README.md found"
else
    echo "⚠️  README.md not found"
fi

echo ""
echo "✅ Package verification complete!"
echo ""
echo "📋 Summary:"
echo "   - Package: $PACKAGE"
echo "   - Size: $(du -h "$PACKAGE" | cut -f1)"
echo ""
echo "💡 Next steps:"
echo "   1. Review the package contents if needed: tar -tzf $PACKAGE"
echo "   2. Test installation: pip install $PACKAGE"
echo "   3. Share with users along with installation instructions"
