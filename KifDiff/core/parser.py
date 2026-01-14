"""KifDiff file parsing and execution."""

import os
import re
from datetime import datetime
from .stats import Stats
from .directives import (
    FileDirective, CreateDirective, DeleteDirective, MoveDirective,
    ReadDirective, TreeDirective, SearchReplaceDirective, DirectiveParams
)
from .directives.overwrite import OverwriteDirective
from utils.output import print_info


def parse_kifdiff(file_path, stats=None, args=None):
    """Parses and executes a .kifdiff file."""
    if stats is None:
        stats = Stats()
    
    # Initialize session backup directory for this run
    global session_backup_dir
    session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_backup_dir = os.path.join(args.backup_dir, f"session_{session_timestamp}")
    
    print_info(f"--- Processing KifDiff file: {file_path} ---")
    if args and not args.no_backup:
        print_info(f"Backup session: {session_backup_dir}")
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        from ..utils.output import print_error
        print_error(f"FATAL ERROR: KifDiff file '{file_path}' not found.")
        stats.failed += 1
        return stats

    # Initialize directive handlers
    file_directive = FileDirective()
    create_directive = CreateDirective()
    overwrite_directive = OverwriteDirective()
    delete_directive = DeleteDirective()
    move_directive = MoveDirective()
    read_directive = ReadDirective()
    tree_directive = TreeDirective()
    search_replace_directive = SearchReplaceDirective()

    current_file = None
    create_file_path = None
    overwrite_file_path = None
    mode = None
    buffer = []
    current_params = DirectiveParams()
    directive_line = 0

    for i, line in enumerate(lines, 1):
        stripped_line = line.strip()

        # If we are inside a content block, buffer everything until we hit an explicit terminator.
        if mode:
            # Check for specific terminators based on the current mode
            is_terminator = False
            
            if mode == "CREATE" and stripped_line == "@Kif END_CREATE":
                is_terminator = True
            elif mode == "OVERWRITE_FILE" and stripped_line == "@Kif END_OVERWRITE_FILE":
                is_terminator = True
            elif mode == "SEARCH_AND_REPLACE" and stripped_line == "@Kif END_SEARCH_AND_REPLACE":
                is_terminator = True
            
            if is_terminator:
                # Finalize the block based on the mode
                if mode == "CREATE":
                    create_directive.execute(create_file_path, "".join(buffer), stats, directive_line, args)
                elif mode == "OVERWRITE_FILE":
                    overwrite_directive.execute(overwrite_file_path, "".join(buffer), stats, directive_line, args)
                elif mode == "SEARCH_AND_REPLACE":
                    full_text = "".join(buffer)
                    try:
                        before_marker = full_text.index("@Kif BEFORE") + len("@Kif BEFORE\n")
                        end_before_marker = full_text.index("@Kif END_BEFORE")
                        after_marker = full_text.index("@Kif AFTER") + len("@Kif AFTER\n")
                        end_after_marker = full_text.index("@Kif END_AFTER")

                        before_text = full_text[before_marker:end_before_marker]
                        after_text = full_text[after_marker:end_after_marker]
                        
                        # Remove trailing newline if present for cleaner matching
                        if before_text.endswith('\n'):
                            before_text = before_text[:-1]
                        if after_text.endswith('\n'):
                            after_text = after_text[:-1]
                        
                        search_replace_directive.execute(current_file, before_text, after_text, current_params, stats, directive_line, args)
                    except (ValueError, IndexError) as e:
                        from ..utils.output import print_error
                        print_error(f"ERROR: Malformed SEARCH_AND_REPLACE block for file '{current_file}' at line {directive_line}.")
                        if args and args.verbose:
                            print(f"  Details: {e}")
                        stats.failed += 1
                
                # Reset state
                mode = None
                buffer = []
                current_params = DirectiveParams()
                continue
            else:
                # Inside a block, treat all lines as content
                buffer.append(line)
                continue

        # --- Outside of content blocks (Global Scope) ---

        if stripped_line.startswith("@Kif FILE"):
            current_file = stripped_line.split(" ", 2)[2]
            file_directive.execute(current_file, stats, args)
            continue

        # Check if this line needs a file context (CREATE can specify its own file)
        needs_file_context = any(stripped_line.startswith(d) for d in [
            "@Kif DELETE", "@Kif SEARCH_AND_REPLACE"
        ])

        if needs_file_context and not current_file:
            from utils.output import print_warning
            print_warning(f"WARNING: No file specified before an operation at line {i}. Skipping.")
            continue

        # Mode Switches with parameters
        if stripped_line.startswith("@Kif CREATE"):
            mode = "CREATE"
            buffer = []
            directive_line = i

            # Extract file path from CREATE directive
            # Format: @Kif CREATE <file_path> or @Kif CREATE(<params>) <file_path>
            parts = stripped_line.split(" ", 2)
            if len(parts) >= 3:
                # File path specified in CREATE directive
                create_file_path = parts[2].strip()
                # Check if there are parameters
                param_match = re.search(r'@Kif CREATE\((.*?)\)\s+(.+)', stripped_line)
                if param_match:
                    current_params = DirectiveParams(param_match.group(1))
                    create_file_path = param_match.group(2).strip()
                else:
                    current_params = DirectiveParams()
            else:
                # No file path in CREATE directive - this is an error
                from utils.output import print_error
                print_error(f"ERROR: No file path specified for CREATE at line {i}. Use: @Kif CREATE <file_path>")
                stats.failed += 1
                mode = None
                continue

            if not create_file_path:
                from utils.output import print_error
                print_error(f"ERROR: No file path specified for CREATE at line {i}. Use: @Kif CREATE <file_path>")
                stats.failed += 1
                mode = None
                continue
            continue

        # OVERWRITE_FILE directive
        if stripped_line.startswith("@Kif OVERWRITE_FILE"):
            mode = "OVERWRITE_FILE"
            buffer = []
            directive_line = i

            # Extract file path from OVERWRITE_FILE directive
            # Format: @Kif OVERWRITE_FILE <file_path>
            parts = stripped_line.split(" ", 2)
            if len(parts) >= 3:
                overwrite_file_path = parts[2].strip()
            else:
                # No file path in OVERWRITE_FILE directive - this is an error
                from utils.output import print_error
                print_error(f"ERROR: No file path specified for OVERWRITE_FILE at line {i}. Use: @Kif OVERWRITE_FILE <file_path>")
                stats.failed += 1
                mode = None
                continue

            if not overwrite_file_path:
                from utils.output import print_error
                print_error(f"ERROR: No file path specified for OVERWRITE_FILE at line {i}. Use: @Kif OVERWRITE_FILE <file_path>")
                stats.failed += 1
                mode = None
                continue
            continue

        if stripped_line.startswith("@Kif DELETE"):
            directive_line = i
            delete_directive.execute(current_file, stats, directive_line, args)
            continue

        if stripped_line.startswith("@Kif MOVE"):
            # Extract source and destination paths
            parts = stripped_line.split(" ", 2)
            if len(parts) < 3:
                from utils.output import print_error
                print_error(f"ERROR: Invalid MOVE directive format at line {i}. Expected: @Kif MOVE <source> <dest>")
                stats.failed += 1
                continue
            source_dest = parts[2]
            if " " not in source_dest:
                from utils.output import print_error
                print_error(f"ERROR: MOVE directive requires both source and destination at line {i}")
                stats.failed += 1
                continue
            source_path, dest_path = source_dest.split(" ", 1)
            directive_line = i
            move_directive.execute(source_path, dest_path, stats, directive_line, args)
            continue
            
        if stripped_line.startswith("@Kif READ"):
            # Extract file path from READ directive
            read_file_path = stripped_line.split(" ", 2)[2] if len(stripped_line.split(" ", 2)) > 2 else ""
            if not read_file_path:
                from utils.output import print_error
                print_error(f"ERROR: No file path specified for READ directive at line {i}.")
                stats.failed += 1
                continue
            directive_line = i
            read_directive.execute(read_file_path, stats, directive_line, args)
            continue

        if stripped_line.startswith("@Kif SEARCH_AND_REPLACE"):
            mode = "SEARCH_AND_REPLACE"
            buffer = []
            directive_line = i
            # Extract parameters if present
            match = re.search(r'@Kif SEARCH_AND_REPLACE\((.*?)\)', stripped_line)
            if match:
                current_params = DirectiveParams(match.group(1))
            else:
                current_params = DirectiveParams()
            continue
        
        if stripped_line.startswith("@Kif TREE"):
            # Extract directory path from TREE directive
            tree_dir = stripped_line.split(" ", 2)[2] if len(stripped_line.split(" ", 2)) > 2 else ""
            if not tree_dir:
                from utils.output import print_error
                print_error(f"ERROR: No directory specified for TREE directive at line {i}.")
                stats.failed += 1
                continue
            # Extract parameters if present
            match = re.search(r'@Kif TREE\((.*?)\)', stripped_line)
            if match:
                current_params = DirectiveParams(match.group(1))
            else:
                current_params = DirectiveParams()
            directive_line = i
            tree_directive.execute(tree_dir, current_params, stats, directive_line, args)
            continue

    print_info("\n--- KifDiff processing complete. ---")

    # Copy accumulated clipboard buffer to clipboard
    if stats.clipboard_buffer:
        try:
            import pyperclip
            combined_content = ''.join(stats.clipboard_buffer)
            pyperclip.copy(combined_content)

            total_items = len(stats.clipboard_files) + len(stats.clipboard_dirs) + len(stats.clipboard_errors)
            from utils.output import print_success, print_warning
            print_success(f"\nClipboard: Copied {total_items} item(s) to clipboard:")
            if stats.clipboard_files:
                print(f"  - {len(stats.clipboard_files)} file(s) read")
            if stats.clipboard_dirs:
                print(f"  - {len(stats.clipboard_dirs)} directory tree(s)")
            if stats.clipboard_errors:
                print_warning(f"  - {len(stats.clipboard_errors)} error(s)")
        except ImportError:
            from utils.output import print_error
            print_error("\nERROR: pyperclip module not installed. Install it with 'pip install pyperclip'")
            print("Content that would have been copied to clipboard:")
            print("="*60)
            print(''.join(stats.clipboard_buffer))
            print("="*60)

    stats.print_summary()
    return stats