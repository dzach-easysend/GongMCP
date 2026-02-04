#!/usr/bin/env python3
"""
Validate test suite structure and syntax.
Run this before installing dependencies to ensure tests are properly structured.
"""

import ast
import sys
from pathlib import Path

def validate_python_file(filepath):
    """Validate a Python file's syntax."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            ast.parse(f.read(), filename=str(filepath))
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    """Validate all test files."""
    test_dir = Path(__file__).parent / "tests"
    
    if not test_dir.exists():
        print("❌ tests/ directory not found")
        return 1
    
    print("🔍 Validating test suite structure...\n")
    
    test_files = list(test_dir.rglob("test_*.py"))
    test_files.extend(list(test_dir.rglob("conftest.py")))
    
    if not test_files:
        print("❌ No test files found")
        return 1
    
    print(f"📁 Found {len(test_files)} test files\n")
    
    errors = []
    for test_file in sorted(test_files):
        rel_path = test_file.relative_to(test_dir.parent)
        is_valid, error = validate_python_file(test_file)
        
        if is_valid:
            print(f"✅ {rel_path}")
        else:
            print(f"❌ {rel_path}: {error}")
            errors.append((rel_path, error))
    
    print()
    
    # Check test structure
    required_dirs = ["unit", "integration", "e2e"]
    for dir_name in required_dirs:
        dir_path = test_dir / dir_name
        if dir_path.exists():
            test_count = len(list(dir_path.glob("test_*.py")))
            print(f"📂 {dir_name}/: {test_count} test files")
        else:
            print(f"⚠️  {dir_name}/: missing")
            errors.append((f"tests/{dir_name}/", "Directory missing"))
    
    print()
    
    if errors:
        print(f"❌ Validation failed with {len(errors)} error(s)")
        return 1
    else:
        print("✅ All test files are syntactically valid!")
        print("\n📝 Next steps:")
        print("   1. Install test dependencies: pip install -e '.[test]'")
        print("   2. Run tests: pytest")
        return 0

if __name__ == "__main__":
    sys.exit(main())
