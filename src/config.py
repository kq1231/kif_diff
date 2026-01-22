"""
KifDiff Configuration
User can override this by creating ~/.kifdiff/config.py or .kifdiff/config.py in project root
"""

import re
from typing import List, Literal
from dataclasses import dataclass

@dataclass
class CommandConfig:
    """Configuration for RUN directive command execution"""
    
    # Mode: "allowlist" (only allowed patterns run) or "blocklist" (everything except blocked runs)
    mode: Literal["allowlist", "blocklist"] = "blocklist"
    
    # Default timeout for commands (seconds)
    default_timeout: int = 30
    
    # Maximum allowed timeout
    max_timeout: int = 300
    
    # Allow shell expansion (e.g., $PATH, ~, wildcards)
    # Default is True so commands with arguments work properly
    allow_shell: bool = True
    
    # Allowed command patterns (regex)
    allowed_patterns: List[str] = None
    
    # Blocked command patterns (regex) - checked regardless of mode
    blocked_patterns: List[str] = None
    
    def __post_init__(self):
        if self.allowed_patterns is None:
            self.allowed_patterns = DEFAULT_ALLOWED_PATTERNS.copy()
        if self.blocked_patterns is None:
            self.blocked_patterns = DEFAULT_BLOCKED_PATTERNS.copy()


# Default safe patterns - common dev commands
DEFAULT_ALLOWED_PATTERNS = [
    # Version control
    r"^git\s+(status|log|diff|branch|checkout|pull|fetch|add|commit|push|clone|stash).*",
    
    # Package managers
    r"^npm\s+(install|test|run|start|build|list|ci).*",
    r"^yarn\s+(install|test|run|start|build|list).*",
    r"^pip\s+(install|list|show|freeze).*",
    r"^cargo\s+(build|test|check|run|clippy).*",
    r"^flutter\s+(pub\s+get|test|build|run|doctor|clean).*",
    r"^poetry\s+(install|run|build|test).*",
    
    # File operations (read-only)
    r"^ls\s+.*",
    r"^cat\s+.*",
    r"^grep\s+.*",
    r"^find\s+.*",
    r"^tree\s+.*",
    r"^head\s+.*",
    r"^tail\s+.*",
    r"^wc\s+.*",
    r"^file\s+.*",
    
    # System info (read-only)
    r"^pwd$",
    r"^whoami$",
    r"^date$",
    r"^uname.*",
    r"^which\s+.*",
    r"^echo\s+.*",
    r"^env$",
    r"^printenv.*",
    
    # Testing/linting
    r"^pytest.*",
    r"^jest.*",
    r"^eslint.*",
    r"^pylint.*",
    r"^black.*",
    r"^flake8.*",
    r"^mypy.*",
    
    # Build tools
    r"^make\s+(build|test|clean)$",
    r"^cmake\s+.*",
    r"^mvn\s+(clean|install|test|package).*",
    r"^gradle\s+(build|test|clean).*",

    # Flutter analyze command
    r"^flutter\s+analzye.*",
]

# Always blocked - dangerous patterns
DEFAULT_BLOCKED_PATTERNS = [
    # Destructive operations
    r".*rm\s+-rf.*",
    r".*rm\s+-fr.*",
    r".*rm\s+.*\*.*",  # rm with wildcards
    r".*rmdir.*",
    r"^dd\s+.*",  # dd command (disk destroyer) - must be at start
    r".*\|\s*dd\s+.*",  # piped to dd
    r".*mkfs.*",
    r".*format.*",
    
    # Privilege escalation
    r".*sudo.*",
    r".*su\s+.*",
    r".*doas.*",
    
    # System modification
    r"^chmod.*777.*",  # chmod 777
    r"^chown\s+.*",  # chown command
    r"^shutdown.*",  # shutdown command
    r"^reboot$",  # reboot command
    r"^halt$",  # halt command
    r"^init\s+[06].*",  # init runlevel change
    
    # Network/security concerns
    r".*curl.*\|.*sh.*",  # Pipe to shell
    r".*wget.*\|.*sh.*",
    r".*>\s*/dev/sd.*",  # Write to disk devices
    r"^eval\s+.*",  # eval command
    r"^exec\s+.*",  # exec command (process replacement)
    r".*;\s*exec\s+.*",  # exec after semicolon
    r".*\|\s*exec\s+.*",  # piped to exec
    
    # Process manipulation
    r"^kill\s+-9.*",  # kill -9
    r"^killall\s+.*",  # killall command
    r"^pkill\s+.*",  # pkill command
    
    # Writing to system directories (not just reading)
    r".*>\s*/etc/.*",  # redirect to /etc
    r".*>\s*/usr/bin/.*",  # redirect to /usr/bin
    r".*>\s*/var/.*",  # redirect to /var
    r".*>\s*/sys/.*",  # redirect to /sys
    r".*>\s*/proc/.*",  # redirect to /proc
    
    # Package removal
    r"^apt\s+(remove|purge|autoremove).*",
    r"^apt-get\s+(remove|purge|autoremove).*",
    r"^yum\s+remove.*",
    r"^brew\s+uninstall.*",
    r"^pip\s+uninstall.*",
]


# Main config instance - users override by importing and modifying
command_config = CommandConfig()


# Helper functions for users to easily customize
def allow_pattern(pattern: str):
    """Add a pattern to allowed list"""
    if pattern not in command_config.allowed_patterns:
        command_config.allowed_patterns.append(pattern)


def block_pattern(pattern: str):
    """Add a pattern to blocked list"""
    if pattern not in command_config.blocked_patterns:
        command_config.blocked_patterns.append(pattern)


def set_mode(mode: Literal["allowlist", "blocklist"]):
    """Change security mode"""
    command_config.mode = mode


def load_user_config():
    """
    Load user config with priority: project > user home > default
    This should be called by main.py on startup.
    """
    import sys
    from pathlib import Path
    
    # Try project-level config
    project_config = Path.cwd() / ".kifdiff" / "config.py"
    if project_config.exists():
        sys.path.insert(0, str(project_config.parent))
        try:
            import config as user_config  # noqa: F401
            sys.path.pop(0)
            return
        except Exception:
            sys.path.pop(0)
    
    # Try user home config
    home_config = Path.home() / ".kifdiff" / "config.py"
    if home_config.exists():
        sys.path.insert(0, str(home_config.parent))
        try:
            import config as user_config  # noqa: F401
            sys.path.pop(0)
            return
        except Exception:
            sys.path.pop(0)
    
    # Use default config (already initialized)
