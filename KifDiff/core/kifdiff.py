"""Core KifDiff application logic."""

import os
from .stats import Stats
from .parser import parse_kifdiff
from utils.output import print_info, print_success, print_error
from utils.notifications import show_notification

def validate_kifdiff(file_path, args):
    """Validate that all operations can be performed without executing them."""
    from utils.output import print_info, print_success, print_error
    
    print_info(f"Validating KifDiff file: {file_path}")
    
    original_dry_run = args.dry_run
    args.dry_run = True
    
    stats = Stats()
    parse_kifdiff(file_path, stats, args)
    
    args.dry_run = original_dry_run
    
    if stats.failed == 0:
        print_success("\n✓ Validation passed! All operations can be performed.")
        return True
    else:
        print_error(f"\n✗ Validation failed! {stats.failed} operation(s) would fail.")
        return False

def process_diff_files(diff_files, args):
    """Process multiple diff files and return aggregated stats."""
    total_stats = Stats()
    
    for diff_file in diff_files:
        if len(diff_files) > 1:
            print(f"\n{'='*60}")
            print_info(f"Processing: {diff_file}")
            print(f"{'='*60}\n")
        
        stats = parse_kifdiff(diff_file, args=args)
        
        # Aggregate stats
        total_stats.created += stats.created
        total_stats.deleted += stats.deleted
        total_stats.modified += stats.modified
        total_stats.failed += stats.failed
        total_stats.skipped += stats.skipped
        total_stats.clipboard_files += stats.clipboard_files
        total_stats.clipboard_dirs += stats.clipboard_dirs
        total_stats.clipboard_errors += stats.clipboard_errors
    
    # Print total stats if multiple files
    if len(diff_files) > 1:
        print(f"\n{'='*60}")
        print_info("TOTAL SUMMARY FOR ALL FILES")
        print(f"{'='*60}")
        total_stats.print_summary()
    
    # Show final notification for clipboard operations
    if total_stats.clipboard_files or total_stats.clipboard_dirs or total_stats.clipboard_errors:
        files_count = len(total_stats.clipboard_files)
        dirs_count = len(total_stats.clipboard_dirs)
        errors_count = len(total_stats.clipboard_errors)
        
        # Build the message based on what was copied
        message_parts = []
        
        if files_count > 0:
            files_list = [os.path.basename(f) for f in total_stats.clipboard_files[:3]]  # Show max 3 files
            if files_count > 3:
                files_list.append(f"... and {files_count - 3} more")
            files_msg = ", ".join(files_list)
            message_parts.append(f"{files_count} file(s)")
            if files_count <= 3:
                message_parts[-1] += f": {files_msg}"
        
        if dirs_count > 0:
            dirs_list = [os.path.basename(d) for d in total_stats.clipboard_dirs[:3]]  # Show max 3 dirs
            if dirs_count > 3:
                dirs_list.append(f"... and {dirs_count - 3} more")
            dirs_msg = ", ".join(dirs_list)
            message_parts.append(f"{dirs_count} director(y/ies)")
            if dirs_count <= 3:
                message_parts[-1] += f": {dirs_msg}"
        
        if errors_count > 0:
            message_parts.append(f"{errors_count} error(s)")
        
        # Set title and notification type based on what happened
        if errors_count > 0 and (files_count > 0 or dirs_count > 0):
            title = "KifDiff - Partial Success"
            notification_type = "warning"
        elif errors_count > 0:
            title = "KifDiff - Errors Only"
            notification_type = "error"
        else:
            title = "KifDiff - Success"
            notification_type = "success"
        
        # Build the final message
        if len(message_parts) == 1:
            message = f"Copied {message_parts[0]} to clipboard."
        else:
            message = f"Copied {', '.join(message_parts[:-1])} and {message_parts[-1]} to clipboard."
        
        show_notification(title, message, notification_type)
    
    # Git integration
    if args.git_commit and not args.dry_run:
        if total_stats.modified > 0 or total_stats.created > 0 or total_stats.deleted > 0:
            print_info("\nCommitting changes to git...")
            try:
                os.system('git add -A')
                os.system(f'git commit -m "{args.git_message}"')
                print_success("Changes committed to git.")
            except Exception as e:
                print_error(f"Git commit failed: {e}")
    
    return total_stats
