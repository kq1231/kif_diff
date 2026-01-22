"""CREATE directive implementation."""

import os
from utils.output import print_info, print_success, print_error, print_warning

class CreateExecutor:
    """Handles @Kif CREATE directive to create files."""
    
    def execute(self, file_path, content, stats, line_num=0, args=None):
        """Creates a file with the given content."""
        print_info(f"[Line {line_num}] CREATE: Creating file '{file_path}'...")
        
        if args and args.dry_run:
            print_warning("DRY RUN: Would create file (no changes made)")
            print(f"Content preview: {content[:100]}..." if len(content) > 100 else content)
            stats.skipped += 1
            return True
        
        if args and args.interactive:
            response = input(f"Create file '{file_path}'? (y/n): ")
            if response.lower() != 'y':
                print_warning("Skipped by user.")
                stats.skipped += 1
                return True
        
        try:
            os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(content)
            print_success("CREATE: Success.")
            stats.created += 1
            return True
        except IOError as e:
            print_error(f"ERROR: Could not create file '{file_path}'. Reason: {e}")
            stats.failed += 1
            return False
