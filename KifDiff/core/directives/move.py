"""MOVE directive implementation."""

import os
import shutil
from utils.output import print_info, print_success, print_error, print_warning

class MoveDirective:
    """Handles @Kif MOVE directive to move/rename files and directories."""
    
    def execute(self, source_path, dest_path, stats, line_num=0, args=None):
        """Moves/renames a file or directory."""
        print_info(f"[Line {line_num}] MOVE: Moving '{source_path}' to '{dest_path}'...")
        
        if not os.path.exists(source_path):
            print_error(f"ERROR: Source '{source_path}' not found. Skipping.")
            stats.failed += 1
            return False
        
        if args and args.dry_run:
            print_warning("DRY RUN: Would move file/directory (no changes made)")
            stats.skipped += 1
            return True
        
        if args and args.interactive:
            response = input(f"Move '{source_path}' to '{dest_path}'? (y/n): ")
            if response.lower() != 'y':
                print_warning("Skipped by user.")
                stats.skipped += 1
                return True
        
        # Backup before moving
        if args and not args.no_backup:
            from utils.backup import backup_file
            if os.path.isfile(source_path):
                backup_file(source_path, args.backup_dir, args)
        
        try:
            # Create destination directory if it doesn't exist
            dest_dir = os.path.dirname(dest_path)
            if dest_dir:
                os.makedirs(dest_dir, exist_ok=True)
            
            # Perform the move
            shutil.move(source_path, dest_path)
            print_success("MOVE: Success.")
            stats.modified += 1
            return True
        except (OSError, shutil.Error) as e:
            print_error(f"ERROR: Could not move '{source_path}' to '{dest_path}'. Reason: {e}")
            stats.failed += 1
            return False
