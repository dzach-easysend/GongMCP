# How to Install Gong MCP Server

Connect your Gong account to Claude Desktop in just a few minutes!

## What You Need

- Claude Desktop installed
- Your Gong account login
- About 5 minutes

## Step 1: Install the Package

**On Windows:**
1. Double-click `install.bat`
2. Wait for "Installation complete!"

**On Mac or Linux:**
1. Double-click `install.sh`
2. If that doesn't work, open Terminal and type: `./install.sh`
3. Wait for "Installation complete!"

That's it! The script does everything for you.

---

**Don't have the script?** Ask the person who gave you this package for the installation script, or see the troubleshooting section below.

## Step 2: Get Your API Keys

You need to copy three keys from your accounts.

### Gong Keys (Required)

1. Log into Gong in your web browser
2. Click your name in the top right
3. Click "Settings" or "Admin"
4. Look for "API" or "Integrations"
5. Copy these two things:
   - **Access Key**
   - **Access Key Secret**

### Anthropic Key (Optional)

Only needed for analyzing lots of calls at once.

1. Go to https://console.anthropic.com/
2. Sign in
3. Click "API Keys"
4. Copy one of your keys

## Step 3: Add to Claude Desktop

### Find the Config File

**Windows:**
1. Press Windows key + R
2. Type: `%APPDATA%\Claude`
3. Press Enter
4. Open `claude_desktop_config.json` with Notepad

**Mac:**
1. Open Finder
2. Press Command + Shift + G
3. Type: `~/Library/Application Support/Claude`
4. Press Enter
5. Open `claude_desktop_config.json` with TextEdit

**Linux:**
1. Open your file manager
2. Go to: `~/.config/Claude/`
3. Open `claude_desktop_config.json` with any text editor

### Add Your Keys

1. **If the file is empty or just has `{}`**, replace everything with this:

```json
{
  "mcpServers": {
    "gong": {
      "command": "gong-mcp",
      "env": {
        "GONG_ACCESS_KEY": "paste_your_gong_key_here",
        "GONG_ACCESS_KEY_SECRET": "paste_your_gong_secret_here",
        "ANTHROPIC_API_KEY": "paste_your_anthropic_key_here"
      }
    }
  }
}
```

2. **If the file already has other servers**, add the `"gong"` part inside `"mcpServers"`:

```json
{
  "mcpServers": {
    "other-server": { ... },
    "gong": {
      "command": "gong-mcp",
      "env": {
        "GONG_ACCESS_KEY": "paste_your_gong_key_here",
        "GONG_ACCESS_KEY_SECRET": "paste_your_gong_secret_here",
        "ANTHROPIC_API_KEY": "paste_your_anthropic_key_here"
      }
    }
  }
}
```

3. **Replace the placeholder text:**
   - Replace `paste_your_gong_key_here` with your actual Gong Access Key
   - Replace `paste_your_gong_secret_here` with your actual Gong Secret
   - Replace `paste_your_anthropic_key_here` with your Anthropic key (or delete this line if you don't have one)

4. **Save the file**

5. **Close Claude Desktop completely** (quit the app)

6. **Open Claude Desktop again**

## Step 4: Try It!

Open Claude Desktop and ask:

> "Show me my Gong calls from the last week"

If Claude shows your calls, you're done! 🎉

## Troubleshooting

### Installation script doesn't work

**Try this:**
1. Go to https://www.python.org/downloads/
2. Download and install Python
3. On Windows: Make sure to check "Add Python to PATH" during installation
4. Run the installation script again

### "Command not found" or "gong-mcp not found"

**Try this:**
1. Open Command Prompt (Windows) or Terminal (Mac/Linux)
2. Go to the folder where you have the files
3. Type: `pip install gong_mcp-0.1.0-py3-none-any.whl`
   *(Replace with the actual filename you have)*
4. Press Enter

### Claude Desktop doesn't work with Gong

**Check these:**
1. Did you save the config file?
2. Did you completely quit and reopen Claude Desktop?
3. Are your keys correct? (No extra spaces, copied completely)
4. If you have multiple servers, is there a comma between them?

### Still not working?

- Double-check all your keys are correct
- Try removing the `ANTHROPIC_API_KEY` line if you don't have one
- Make sure the config file is in the right location
- Make sure you restarted Claude Desktop completely

## Need More Help?

Check the main [README.md](README.md) file for more details.
