# How to Install Gong MCP Server

Connect your Gong account to Claude Desktop (or Cursor) in just a few minutes.

## What You Need

- **Claude Desktop** or **Cursor** installed
- **Python 3.10 or higher** ([python.org](https://www.python.org/downloads/))
- Your **Gong** account login
- About 5 minutes

## Step 1: Install the Package

### Option A: Using the install script (when you have a .whl file)

If someone gave you a `.whl` file (e.g. `gong_mcp-0.1.0-py3-none-any.whl`):

**On Windows:**
1. Put the `.whl` file in the same folder as `install.bat` (or in Downloads/Desktop)
2. Double-click `install.bat`
3. Wait for "Installation complete!"

**On Mac or Linux:**
1. Put the `.whl` file in the same folder as `install.sh` (or in Downloads/Desktop)
2. Run: `./install.sh` (or double-click `install.sh`)
3. If you get "permission denied", run: `chmod +x install.sh` then `./install.sh`
4. Wait for "Installation complete!"

You can also pass the path to the wheel: `./install.sh /path/to/gong_mcp-0.1.0-py3-none-any.whl`

### Option B: Install from PyPI (no .whl file needed)

If the package is published on PyPI:

```bash
pip install gong-mcp
# or
pip3 install gong-mcp
```

### Option C: Manual install from a .whl file

```bash
pip install gong_mcp-0.1.0-py3-none-any.whl
# Use the actual .whl filename you have
```

**Don't have the script or .whl?** Ask the person who gave you this package, or use Option B if the package is on PyPI. See [Troubleshooting](#troubleshooting) below.

## Step 2: Get Your API Keys

You need to copy keys from your accounts.

### Gong Keys (Required)

1. Log into Gong in your web browser
2. Click your name in the top right
3. Click **Settings** or **Admin**
4. Look for **API** or **Integrations**
5. Copy:
   - **Access Key**
   - **Access Key Secret**

### Anthropic Key (Optional)

Only needed for analyzing many calls at once (batch analysis).

1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Sign in → **API Keys**
3. Copy one of your keys

## Step 3: Add to Claude Desktop or Cursor

### Claude Desktop: Find the config file

| OS      | Path |
|---------|------|
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Mac     | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Linux   | `~/.config/Claude/claude_desktop_config.json` |

**Windows:** Win + R → type `%APPDATA%\Claude` → Enter → open `claude_desktop_config.json` in Notepad  
**Mac:** Finder → Cmd + Shift + G → `~/Library/Application Support/Claude` → open `claude_desktop_config.json` in TextEdit  
**Linux:** Open `~/.config/Claude/claude_desktop_config.json` in any text editor

### Cursor

Cursor uses its own MCP settings. For full Cursor setup (including from-source and cross-MCP usage), see **[CURSOR_SETUP.md](CURSOR_SETUP.md)**. The config shape is the same: `command: "gong-mcp"` and the same `env` keys.

### Add your keys

1. **If the file is empty or just `{}`**, replace everything with:

```json
{
  "mcpServers": {
    "gong": {
      "command": "gong-mcp",
      "env": {
        "GONG_ACCESS_KEY": "paste_your_gong_access_key_here",
        "GONG_ACCESS_KEY_SECRET": "paste_your_gong_secret_here",
        "ANTHROPIC_API_KEY": "paste_your_anthropic_key_here",
        "DIRECT_LLM_TOKEN_LIMIT": "100"
      }
    }
  }
}
```

2. **If the file already has other servers**, add the `"gong"` block inside `"mcpServers"` (with a comma after the previous server):

```json
{
  "mcpServers": {
    "other-server": { ... },
    "gong": {
      "command": "gong-mcp",
      "env": {
        "GONG_ACCESS_KEY": "paste_your_gong_access_key_here",
        "GONG_ACCESS_KEY_SECRET": "paste_your_gong_secret_here",
        "ANTHROPIC_API_KEY": "paste_your_anthropic_key_here",
        "DIRECT_LLM_TOKEN_LIMIT": "100"
      }
    }
  }
}
```

3. **Replace the placeholders:**
   - `paste_your_gong_access_key_here` → your Gong Access Key
   - `paste_your_gong_secret_here` → your Gong Access Key Secret
   - `paste_your_anthropic_key_here` → your Anthropic key (or remove this line if you don’t use batch analysis)
   - `DIRECT_LLM_TOKEN_LIMIT` → Token threshold in K (default 100 = 100K tokens). Set to 0 to always use direct mode.

4. **Save the file**

5. **Quit Claude Desktop (or Cursor) completely**, then open it again

## Step 4: Try it

In Claude Desktop or Cursor, ask:

> "Show me my Gong calls from the last week"

If you see your calls, you’re done.

## Troubleshooting

### Installation script doesn’t work or no .whl found

- Install **Python 3.10+** from [python.org](https://www.python.org/downloads/)
- **Windows:** During setup, check **"Add Python to PATH"**
- Then run the install script again, or use: `pip install gong-mcp` (Option B above)

### "Command not found" or "gong-mcp not found"

1. Open Command Prompt (Windows) or Terminal (Mac/Linux)
2. Install the package:
   - From PyPI: `pip install gong-mcp` or `pip3 install gong-mcp`
   - From a .whl: `pip install gong_mcp-0.1.0-py3-none-any.whl` (use your actual filename)
3. Restart the terminal (and Claude Desktop or Cursor)

### Claude Desktop / Cursor doesn’t see Gong

- Did you **save** the config file?
- Did you **fully quit and reopen** the app?
- Are the keys correct? (no extra spaces, full copy)
- If you have multiple servers, is there a **comma** between each server block?

### "Module not found" or Python errors

- Check version: `python3 --version` (must be 3.10 or higher)
- Reinstall: `pip install --upgrade gong-mcp`

### Still not working

- Verify all keys (Gong and optional Anthropic)
- Remove the `ANTHROPIC_API_KEY` line if you don’t use batch analysis
- Confirm the config file path for your OS (see Step 3)
- Restart the AI app completely after any config change

## Need more help?

- **Claude Desktop:** See the main [README.md](../README.md)
- **Cursor:** See [CURSOR_SETUP.md](CURSOR_SETUP.md) for Cursor-specific setup and cross-MCP usage
