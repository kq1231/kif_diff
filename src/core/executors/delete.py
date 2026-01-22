"""DELETE directive implementation."""

import os
from utils.output import print_info, print_success, print_error, print_warning

class DeleteExecutor:
    """Handles @Kif DELETE directive to delete files."""
    
    def execute(self, file_path, stats, line_num=0, args=None):
        """Deletes the specified file."""
        print_info(f"[Line {line_num}] DELETE: Deleting file '{file_path}'...")
        
        if not os.path.exists(file_path):
            print_warning(f"WARNING: File '{file_path}' not found. Skipping.")
            stats.skipped += 1
            return True
        
        if args and args.dry_run:
            print_warning("DRY RUN: Would delete file (no changes made)")
            stats.skipped += 1
            return True
        
        if args and args.interactive:
            response = input(f"Delete file '{file_path}'? (y/n): ")
            if response.lower() != 'y':
                print_warning("Skipped by user.")
                stats.skipped += 1
                return True
        
        # Backup before deleting
        if args and not args.no_backup:
            from utils.backup import backup_file
            backup_file(file_path, args.backup_dir, args)
        
        try:
            os.remove(file_path)
            print_success("DELETE: Success.")
            stats.deleted += 1
            return True
        except OSError as e:
            print_error(f"ERROR: Could not delete file '{file_path}'. Reason: {e}")
            stats.failed += 1
            return False
