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
    
    # Show notification for all script runs
    # Calculate totals
    total_successful = total_stats.created + total_stats.modified + total_stats.deleted
    files_count = len(total_stats.clipboard_files)
    dirs_count = len(total_stats.clipboard_dirs)
    errors_count = len(total_stats.clipboard_errors)
    
    # Build notification based on stats
    message_parts = []
    
    # Add operation breakdown
    if total_stats.created > 0:
        message_parts.append(f"{total_stats.created} created")
    if total_stats.modified > 0:
        message_parts.append(f"{total_stats.modified} modified")
    if total_stats.deleted > 0:
        message_parts.append(f"{total_stats.deleted} deleted")
    if total_stats.skipped > 0:
        message_parts.append(f"{total_stats.skipped} skipped")
    
    # Add clipboard info if relevant
    if files_count > 0 or dirs_count > 0:
        clipboard_parts = []
        if files_count > 0:
            clipboard_parts.append(f"{files_count} file(s)")
        if dirs_count > 0:
            clipboard_parts.append(f"{dirs_count} tree(s)")
        if clipboard_parts:
            message_parts.append(f"clipboard: {', '.join(clipboard_parts)}")
    
    # Set title and notification type based on what happened
    if total_stats.failed > 0:
        title = "KifDiff - Failed"
        notification_type = "error"
        if total_successful > 0:
            message = f"{total_stats.failed} failed, {total_successful} succeeded"
        else:
            message = f"{total_stats.failed} operation(s) failed"
        if message_parts:
            message += f" ({', '.join(message_parts)})"
    elif total_stats.skipped > 0 and total_successful > 0:
        title = "KifDiff - Partial Success"
        notification_type = "warning"
        message = f"{total_successful} operations succeeded"
        if message_parts:
            message += f" ({', '.join(message_parts)})"
    elif total_successful == 0:
        # No file operations performed (maybe just READ/TREE)
        if files_count > 0 or dirs_count > 0:
            title = "KifDiff - Inquiry Complete"
            notification_type = "info"
            message = ', '.join(message_parts).capitalize() if message_parts else "Inquiry completed"
        else:
            title = "KifDiff - No Changes"
            notification_type = "info"
            message = "No operations performed"
    else:
        title = "KifDiff - Success"
        notification_type = "success"
        message = f"{total_successful} operations succeeded"
        if message_parts:
            message += f" ({', '.join(message_parts)})"
    
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
