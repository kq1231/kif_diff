"""OVERWRITE_FILE directive implementation."""

import os
from utils.output import print_info, print_success, print_error, print_warning
from utils.backup import backup_file

class OverwriteDirective:
    """Handles @Kif OVERWRITE_FILE directive to completely replace file contents."""
    
    def execute(self, file_path, content, stats, line_num=0, args=None):
        """Overwrites an existing file with new content (or creates if doesn't exist)."""
        print_info(f"[Line {line_num}] OVERWRITE_FILE: Overwriting file '{file_path}'...")
        
        if args and args.dry_run:
            print_warning("DRY RUN: Would overwrite file (no changes made)")
            if args.verbose:
                print("Content preview:", content[:100] + "..." if len(content) > 100 else content)
            stats.skipped += 1
            return True
        
        file_exists = os.path.exists(file_path)
        
        # Backup existing file if it exists and backups are enabled
        if file_exists and args and not args.no_backup:
            backup_file(file_path, args.backup_dir)
        
        # Create parent directories if they don't exist
        parent_dir = os.path.dirname(file_path)
        if parent_dir and not os.path.exists(parent_dir):
            try:
                os.makedirs(parent_dir)
                print_info(f"Created parent directory: {parent_dir}")
            except OSError as e:
                print_error(f"ERROR: Could not create parent directory '{parent_dir}'. Reason: {e}")
                stats.failed += 1
                return False
        
        # Write the new content
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            
            if file_exists:
                print_success(f"OVERWRITE_FILE: File '{file_path}' overwritten successfully.")
            else:
                print_success(f"OVERWRITE_FILE: File '{file_path}' created successfully.")
            
            stats.modified += 1
            return True
            
        except IOError as e:
            print_error(f"ERROR: Could not write to file '{file_path}'. Reason: {e}")
            stats.failed += 1
            return False

