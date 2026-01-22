"""Executor for RUN directive - executes terminal commands with security controls."""

import subprocess
import re
from pathlib import Path
from utils.output import print_error, print_success, print_info

def execute_run(directive, stats, args):
    """Execute a terminal command with allowlist/blocklist checking."""
    from config import command_config
    
    command = directive.command
    timeout = directive.params.get('timeout', command_config.default_timeout)
    # Use shell=True by default so commands with arguments work properly
    shell = directive.params.get('shell', True)
    cwd = directive.params.get('cwd', None)
    
    # Enforce max timeout
    if timeout > command_config.max_timeout:
        timeout = command_config.max_timeout
    
    if args.verbose:
        print_info(f"RUN: {command}")
        print_info(f"  Timeout: {timeout}s, Shell: {shell}, CWD: {cwd if cwd else 'current directory'}")
    
    # Check if command is allowed
    allowed, reason = is_command_allowed(command)
    
    if not allowed:
        print_error(f"✗ COMMAND DENIED: {command}")
        print_error(f"  Reason: {reason}")
        
        # Add to clipboard buffer
        result_output = f"""{'='*80}
Command: {command}
Status: ✗ DENIED
Reason: {reason}
{'='*80}
"""
        stats.clipboard_buffer.append(result_output)
        stats.clipboard_errors.append(command)
        stats.failed += 1
        return
    
    # Dry run mode
    if args.dry_run:
        print_info(f"[DRY RUN] Would execute: {command}")
        return
    
    # Execute the command
    try:
        # Determine working directory
        if cwd:
            working_dir = Path(cwd).expanduser().resolve()
            if not working_dir.exists():
                print_error(f"✗ Working directory does not exist: {working_dir}")
                stats.failed += 1
                return
            print_info(f"Executing in: {working_dir}")
            print_info(f"Command: {command}")
        else:
            working_dir = Path.cwd()
            print_info(f"Executing: {command}")
        
        result = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(working_dir)
        )
        
        # Format output
        status_symbol = "✓" if result.returncode == 0 else "✗"
        status_text = "SUCCESS" if result.returncode == 0 else "FAILED"
        
        # Print result
        if result.returncode == 0:
            print_success(f"{status_symbol} Command succeeded (exit code: {result.returncode})")
        else:
            print_error(f"{status_symbol} Command failed (exit code: {result.returncode})")
        
        # Show stdout if present
        if result.stdout:
            print("\nOutput:")
            print("-" * 80)
            print(result.stdout)
            print("-" * 80)
        
        # Show stderr if present
        if result.stderr:
            print("\nErrors:")
            print("-" * 80)
            print(result.stderr)
            print("-" * 80)
        
        # Format for clipboard
        clipboard_output = f"""{'='*80}
Command: {command}
Working Directory: {working_dir}
Status: {status_symbol} {status_text} (exit code: {result.returncode})
{'='*80}
"""
        if result.stdout:
            clipboard_output += f"\nOutput:\n{result.stdout}\n"
        
        if result.stderr:
            clipboard_output += f"\nErrors:\n{result.stderr}\n"
        
        clipboard_output += "=" * 80 + "\n"
        
        stats.clipboard_buffer.append(clipboard_output)
        
        if result.returncode == 0:
            stats.modified += 1  # Count as successful operation
        else:
            stats.failed += 1
        
    except subprocess.TimeoutExpired as e:
        print_error(f"✗ COMMAND TIMEOUT: Command exceeded {timeout} seconds")
        
        # Include any partial output in clipboard
        stdout_partial = e.stdout.decode('utf-8') if e.stdout else ''
        stderr_partial = e.stderr.decode('utf-8') if e.stderr else ''
        
        timeout_output = f"""{'='*80}
Command: {command}
Working Directory: {working_dir}
Status: ✗ TIMEOUT
Timeout: {timeout} seconds
{'='*80}
"""
        if stdout_partial:
            timeout_output += f"\nPartial Output:\n{stdout_partial}\n"
        if stderr_partial:
            timeout_output += f"\nPartial Errors:\n{stderr_partial}\n"
        timeout_output += "=" * 80 + "\n"
        
        stats.clipboard_buffer.append(timeout_output)
        stats.clipboard_errors.append(command)
        stats.failed += 1
        
    except Exception as e:
        print_error(f"✗ COMMAND ERROR: {e}")
        
        error_output = f"""{'='*80}
Command: {command}
Working Directory: {working_dir if 'working_dir' in locals() else Path.cwd()}
Status: ✗ ERROR
Error: {str(e)}
{'='*80}
"""
        stats.clipboard_buffer.append(error_output)
        stats.clipboard_errors.append(command)
        stats.failed += 1


def is_command_allowed(command: str) -> tuple[bool, str]:
    """
    Check if a command is allowed based on config patterns.
    Returns (allowed: bool, reason: str)
    """
    from config import command_config
    
    # Always check blocked patterns first (regardless of mode)
    for pattern in command_config.blocked_patterns:
        if re.match(pattern, command):
            return False, f"Command matches blocked pattern: {pattern}"
    
    # In allowlist mode, command must match an allowed pattern
    if command_config.mode == "allowlist":
        for pattern in command_config.allowed_patterns:
            if re.match(pattern, command):
                return True, "Command matches allowed pattern"
        return False, "Command does not match any allowed pattern"
    
    # In blocklist mode, if not blocked, it's allowed
    return True, "Command is allowed in blocklist mode"
