#!/usr/bin/env python3
"""KifDiff: A powerful file modification tool with safety features."""

import os
import sys
import argparse

# Import core modules
from core.kif_diff import validate_kifdiff, process_diff_files
from utils.backup import list_backup_sessions, rollback_backups
from utils.output import print_error, print_info

# Load user config for RUN directive
from config import load_user_config
load_user_config()

def main():
    parser = argparse.ArgumentParser(
        description="KifDiff: A powerful file modification tool with safety features.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s changes.kifdiff                    # Apply changes
  %(prog)s changes.kifdiff --dry-run          # Preview changes
  %(prog)s changes.kifdiff --validate         # Validate without applying
  %(prog)s changes.kifdiff -i                 # Interactive mode
  %(prog)s --rollback                         # Undo last changes
  %(prog)s --list-sessions                    # List all backup sessions
  %(prog)s --rollback-session session_XXX     # Restore specific session
  %(prog)s file1.kifdiff file2.kifdiff        # Apply multiple files

Directives:
  @Kif FILE <path>                            # Set target file for operations
  @Kif CREATE                                 # Create a new file
  @Kif DELETE                                 # Delete the target file
  @Kif MOVE <source> <dest>                   # Move/rename files or directories
  @Kif READ <path>                            # Read file content to clipboard
  @Kif TREE <dir>                             # Copy directory tree structure to clipboard
  @Kif SEARCH_AND_REPLACE                     # Replace content in file
  @Kif RUN <command>                          # Execute terminal command (with security controls)
  @Kif OVERWRITE_FILE <path>                  # Overwrite file content
  @Kif FIND <path>                            # Find files and directories

Directive Parameters:
  @Kif SEARCH_AND_REPLACE(replace_all=true, ignore_whitespace=false)
  @Kif TREE(depth=3, show_hidden=false, include_files=true)
  
  Available parameters for SEARCH_AND_REPLACE:
    - replace_all: Replace all occurrences (default: false)
    - ignore_whitespace: Ignore trailing whitespace (default: false)
    - fuzzy_match: Use fuzzy matching (default: false)
    - regex: Use regular expressions (default: false)
    - count: Number of replacements (default: 1)
  
  Available parameters for TREE:
    - depth: Maximum depth to display (default: unlimited)
    - show_hidden: Show hidden files/directories (default: false)
    - include_files: Show files in tree (default: true)
    - Note: Tree structure is copied to clipboard, not displayed
  
  Available parameters for RUN:
    - timeout: Command timeout in seconds (default: 30, max: 300)
    - shell: Enable shell mode for command parsing (default: true)
    - cwd: Working directory for command execution (default: current directory)
    - Note: Default mode is blocklist (all commands allowed except blocked patterns)
    - Note: Always specify cwd when working in project subdirectories
        """
    )

    
    # Positional arguments
    parser.add_argument("diff_file", nargs='*', 
                       help="One or more .kifdiff files to apply")
    
    # Safety features
    parser.add_argument("--dry-run", action="store_true",
                       help="Preview changes without modifying files")
    parser.add_argument("--validate", action="store_true",
                       help="Validate all operations can be performed")
    parser.add_argument("-i", "--interactive", action="store_true",
                       help="Ask for confirmation before each operation")
    parser.add_argument("--no-backup", action="store_true",
                       help="Skip creating backup files")
    
    # Utility features
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Show detailed information during processing")
    parser.add_argument("--rollback", action="store_true",
                       help="Restore files from most recent backups")
    parser.add_argument("--list-sessions", action="store_true",
                       help="List all backup sessions")
    parser.add_argument("--rollback-session",
                       help="Restore files from a specific backup session")
    parser.add_argument("--backup-dir", default=".kif_backups",
                       help="Directory for backup files (default: .kif_backups)")
    
    # Git integration
    parser.add_argument("--git-commit", action="store_true",
                       help="Automatically commit changes to git after applying")
    parser.add_argument("--git-message", default="Applied KifDiff changes",
                       help="Git commit message (default: 'Applied KifDiff changes')")
    
    args = parser.parse_args()
    
    # Handle list sessions
    if args.list_sessions:
        sessions = list_backup_sessions(args.backup_dir)
        if not sessions:
            print_error("No backup sessions found.")
            sys.exit(1)
        
        print_info("Available backup sessions:")
        for i, session in enumerate(sessions, 1):
            print(f"  {i}. {session['name']} ({session['files']} file(s))")
        print(f"\nTo restore a session, use: --rollback-session {sessions[0]['name']}")
        sys.exit(0)
    
    # Handle rollback
    if args.rollback:
        rollback_backups(args.backup_dir)
        sys.exit(0)
    
    # Handle specific session rollback
    if args.rollback_session:
        rollback_backups(args.backup_dir, args.rollback_session)
        sys.exit(0)
    
    # Require at least one diff file
    if not args.diff_file:
        parser.print_help()
        sys.exit(1)
    
    # Validate all files exist
    for diff_file in args.diff_file:
        if not os.path.exists(diff_file):
            print_error(f"FATAL ERROR: The specified .kifdiff file '{diff_file}' does not exist.")
            sys.exit(1)
    
    # Validation mode
    if args.validate:
        all_valid = True
        for diff_file in args.diff_file:
            if not validate_kifdiff(diff_file, args):
                all_valid = False
        sys.exit(0 if all_valid else 1)
    
    # Process all diff files
    total_stats = process_diff_files(args.diff_file, args)
    
    # Exit with appropriate code
    sys.exit(0 if total_stats.failed == 0 else 1)

if __name__ == "__main__":
    main()