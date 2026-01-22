# KifDiff 🚀

A powerful, LLM-friendly file modification tool with built-in safety features and command execution capabilities.

## ✨ Features

- **Safe File Operations**: Automatic backups, dry-run mode, and rollback support
- **Multiple Operations**: Create, delete, move, search & replace, overwrite files
- **Inquiry System**: Read files, explore directory trees, find files by pattern
- **Command Execution**: Run terminal commands with security controls (NEW!)
- **LLM Optimized**: Designed for AI assistants like Claude to generate modifications
- **Interactive Mode**: Review changes before applying
- **Rich Output**: Beautiful terminal output with progress indicators

## 📦 Installation

```bash
# Clone the repository
git clone <repository-url>
cd kif_diff

# Install dependencies
pip install -r requirements.txt
```

## 🚀 Quick Start

### Basic Usage

```bash
# Apply changes from a .kifdiff file
python3 src/main.py changes.kifdiff

# Preview changes without applying (dry-run)
python3 src/main.py changes.kifdiff --dry-run

# Interactive mode (confirm each operation)
python3 src/main.py changes.kifdiff -i

# Validate syntax without executing
python3 src/main.py changes.kifdiff --validate
```

### Rollback Changes

```bash
# Undo the most recent changes
python3 src/main.py --rollback

# List all backup sessions
python3 src/main.py --list-sessions

# Restore a specific session
python3 src/main.py --rollback-session session_20240122_123456
```

## 📝 KifDiff Syntax

### File Operations

#### Create File
```text
@Kif CREATE /path/to/file.txt
This is the content
of the new file.
@Kif END_CREATE
```

#### Delete File
```text
@Kif DELETE /path/to/file.txt
```

#### Move/Rename File or Directory
```text
@Kif MOVE /old/path/file.txt /new/path/file.txt
```

#### Overwrite File
```text
@Kif OVERWRITE_FILE /path/to/file.txt
Completely new content
that replaces everything.
@Kif END_OVERWRITE_FILE
```

#### Search and Replace
```text
@Kif SEARCH_AND_REPLACE /path/to/file.txt
@Kif BEFORE
old content to find
@Kif END_BEFORE
@Kif AFTER
new content to replace with
@Kif END_AFTER
@Kif END_SEARCH_AND_REPLACE
```

**Multiple replacements in same file:**
```text
@Kif SEARCH_AND_REPLACE /path/to/file.txt
@Kif BEFORE
first old content
@Kif END_BEFORE
@Kif AFTER
first new content
@Kif END_AFTER
@Kif BEFORE
second old content
@Kif END_BEFORE
@Kif AFTER
second new content
@Kif END_AFTER
@Kif END_SEARCH_AND_REPLACE
```

**With parameters:**
```text
# Replace all occurrences
@Kif SEARCH_AND_REPLACE(replace_all=true) /path/to/file.txt

# Use regex
@Kif SEARCH_AND_REPLACE(regex=true, replace_all=true) /path/to/file.txt

# Ignore whitespace differences
@Kif SEARCH_AND_REPLACE(ignore_whitespace=true) /path/to/file.txt
```

### Inquiry Operations

#### Read File
```text
@Kif READ /path/to/file.txt
```
Copies file content to clipboard.

#### Directory Tree
```text
@Kif TREE /path/to/directory

# With parameters
@Kif TREE(depth=2, show_hidden=false) /path/to/directory
```
Copies directory structure to clipboard.

#### Find Files
```text
@Kif FIND(match_pattern=".*\.py$") /path/to/search

# With exclusions
@Kif FIND(match_pattern=".*\.js$", exclude="node_modules|dist") /path/to/search
```

### Command Execution (NEW! 🎉)

#### Run Commands
```text
# Basic command
@Kif RUN git status

# With timeout
@Kif RUN(timeout=60) npm install

# Shell is enabled by default, so commands with arguments work naturally
@Kif RUN echo $PATH

# With working directory (IMPORTANT for project-specific commands)
@Kif RUN(cwd="/path/to/project") npm install
@Kif RUN(cwd="~/projects/myapp") flutter pub get

# Combined parameters
@Kif RUN(cwd="/path/to/project", timeout=120) npm run build

# Multiple commands in same directory
@Kif RUN(cwd="/path/to/flutter/project") flutter pub get
@Kif RUN(cwd="/path/to/flutter/project") flutter test
@Kif RUN(cwd="/path/to/flutter/project") flutter build apk
```

#### Security Features

Commands are filtered by **blocklist** patterns in `config.py`:

**Default Mode: Blocklist**
- All commands are allowed by default
- Only blocked patterns are prevented from running
- Maximum flexibility with safety guardrails

**Always Blocked (Dangerous Operations):**
- Destructive: `rm -rf`, `dd`, `format`
- Privilege escalation: `sudo`, `su`
- System modification: `chmod 777`, `shutdown`, `reboot`
- Dangerous patterns: `curl | sh`, `eval`, `kill -9`

#### Custom Configuration

Create `.kifdiff/config.py` in your project:

```python
from config import allow_pattern, block_pattern, set_mode

# Allow additional commands
allow_pattern(r"^docker\s+(build|run|ps).*")
allow_pattern(r"^make\s+(build|test).*")

# Block specific patterns
block_pattern(r".*production.*")

# Change to allowlist mode (only allow specific patterns)
set_mode("allowlist")

# Adjust timeout defaults
from config import command_config
command_config.default_timeout = 60
```

Or create `~/.kifdiff/config.py` for global settings.

## 🎯 Use Cases

### 1. Automated Refactoring
```text
@Kif SEARCH_AND_REPLACE(replace_all=true) /src/app.js
@Kif BEFORE
var 
@Kif END_BEFORE
@Kif AFTER
const 
@Kif END_AFTER
@Kif END_SEARCH_AND_REPLACE
```

### 2. Project Setup
```text
@Kif RUN git clone https://github.com/user/repo.git
@Kif RUN cd repo && npm install
@Kif RUN npm run build
```

### 3. Feature Implementation
```text
# Create new component
@Kif CREATE /src/components/Button.js
export default function Button() {
  return <button>Click me</button>;
}
@Kif END_CREATE

# Run tests
@Kif RUN npm test Button
```

### 4. Batch Updates
```text
@Kif FIND(match_pattern=".*\.test\.js$") /src
# Then use results to create SEARCH_AND_REPLACE for all test files
```

## 🛡️ Safety Features

- **Automatic Backups**: Every modification creates a timestamped backup
- **Dry Run Mode**: Preview changes before applying (`--dry-run`)
- **Interactive Mode**: Confirm each operation (`-i`)
- **Validation**: Check syntax without executing (`--validate`)
- **Rollback**: Restore previous state instantly (`--rollback`)
- **Command Security**: Allowlist/blocklist for terminal commands
- **Timeout Protection**: Commands auto-terminate after timeout

## 🔧 Advanced Options

```bash
# Verbose output for debugging
python3 src/main.py changes.kifdiff -v

# Skip backups (not recommended)
python3 src/main.py changes.kifdiff --no-backup

# Custom backup directory
python3 src/main.py changes.kifdiff --backup-dir /custom/path

# Git integration
python3 src/main.py changes.kifdiff --git-commit --git-message "Applied changes"

# Multiple files at once
python3 src/main.py file1.kifdiff file2.kifdiff file3.kifdiff
```

## 💡 Tips for LLM Usage

When working with AI assistants like Claude:

1. **Skip inquiry if context exists**: If file contents are already in the conversation, go straight to execution
2. **Use minimal changes**: Prefer `SEARCH_AND_REPLACE` over rewriting entire files
3. **Group related changes**: Use multiple BEFORE/AFTER blocks in one SEARCH_AND_REPLACE
4. **Automate workflows**: Chain commands with RUN directives
5. **Always use absolute paths**: Never use relative paths

## 📄 Comments

Comments are supported! Use `#` for single-line comments:

```text
# This is a comment
@Kif CREATE /path/to/file.txt
Content here
@Kif END_CREATE

# Another comment
@Kif RUN npm test
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🙏 Acknowledgments

Built with love for AI-assisted development workflows.

---

**Made with ❤️ by Abu Hurayrah**