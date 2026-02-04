#!/bin/bash
# Simple installation script for Mac and Linux

echo "Installing Gong MCP Server..."
echo ""

# Check if .whl file was provided as argument
if [ -n "$1" ]; then
    WHEEL_FILE="$1"
    if [ ! -f "$WHEEL_FILE" ]; then
        echo "Error: File not found: $WHEEL_FILE"
        exit 1
    fi
else
    # Try to find the wheel file in common locations
    WHEEL_FILE=""
    
    # Current directory
    if [ -z "$WHEEL_FILE" ]; then
        WHEEL_FILE=$(ls *.whl 2>/dev/null | head -1)
    fi
    
    # Script's directory
    if [ -z "$WHEEL_FILE" ]; then
        SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
        WHEEL_FILE=$(ls "$SCRIPT_DIR"/*.whl 2>/dev/null | head -1)
    fi
    
    # Downloads folder
    if [ -z "$WHEEL_FILE" ]; then
        WHEEL_FILE=$(ls ~/Downloads/*.whl 2>/dev/null | head -1)
    fi
    
    # Desktop
    if [ -z "$WHEEL_FILE" ]; then
        WHEEL_FILE=$(ls ~/Desktop/*.whl 2>/dev/null | head -1)
    fi
    
    if [ -z "$WHEEL_FILE" ]; then
        echo "Error: Could not find the .whl file."
        echo ""
        echo "Please either:"
        echo "1. Put the .whl file in the same folder as this script, or"
        echo "2. Run: ./install.sh /path/to/gong_mcp-0.1.0-py3-none-any.whl"
        echo "3. Or use the manual installation method in INSTALL.md"
        exit 1
    fi
fi

echo "Found: $WHEEL_FILE"
echo ""

# Try different pip commands
if command -v pip3 &> /dev/null; then
    echo "Installing with pip3..."
    pip3 install "$WHEEL_FILE"
elif command -v pip &> /dev/null; then
    echo "Installing with pip..."
    pip install "$WHEEL_FILE"
elif command -v python3 &> /dev/null; then
    echo "Installing with python3 -m pip..."
    python3 -m pip install "$WHEEL_FILE"
elif command -v python &> /dev/null; then
    echo "Installing with python -m pip..."
    python -m pip install "$WHEEL_FILE"
else
    echo "Error: Could not find Python or pip."
    echo "Please install Python from https://www.python.org/downloads/"
    exit 1
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Installation complete!"
    echo ""
    echo "Next steps:"
    echo "1. Get your API keys from Gong and Anthropic"
    echo "2. Add them to Claude Desktop config file"
    echo "3. See INSTALL.md for detailed instructions"
else
    echo ""
    echo "❌ Installation failed. Please check the error messages above."
    exit 1
fi
