"""TREE directive implementation."""

import os
from utils.output import print_info, print_success, print_error, print_warning, print_tree

class TreeExecutor:
    """Handles @Kif TREE directive to show directory structure."""
    
    def execute(self, dir_path, params, stats, line_num=0, args=None):
        """Displays directory tree structure and copies it to clipboard."""
        print_info(f"[Line {line_num}] TREE: Showing tree for '{dir_path}'...")
        
        if not os.path.exists(dir_path):
            error_msg = f"ERROR: Directory '{dir_path}' not found. Skipping."
            print_error(error_msg)
            stats.failed += 1

            # Append error to clipboard buffer
            formatted_error = f"===== TREE ERROR: {dir_path} =====\n{error_msg}\n\n"
            stats.clipboard_buffer.append(formatted_error)
            stats.clipboard_errors.append(f"TREE: {dir_path}")
            return False
        
        if not os.path.isdir(dir_path):
            error_msg = f"ERROR: '{dir_path}' is not a directory. Skipping."
            print_error(error_msg)
            stats.failed += 1

            # Append error to clipboard buffer
            formatted_error = f"===== TREE ERROR: {dir_path} =====\n{error_msg}\n\n"
            stats.clipboard_buffer.append(formatted_error)
            stats.clipboard_errors.append(f"TREE: {dir_path}")
            return False
        
        # Get parameters
        max_depth = params.get('depth', None)
        show_hidden = params.get('show_hidden', False)
        include_files = params.get('include_files', True)
        
        if args and args.verbose:
            print(f"  Parameters: depth={max_depth}, show_hidden={show_hidden}, include_files={include_files}")
        
        def get_tree_structure(path, prefix="", depth=0):
            """Recursively build tree structure."""
            if max_depth is not None and depth >= max_depth:
                return []
            
            items = []
            try:
                entries = sorted(os.listdir(path))
                if not show_hidden:
                    entries = [e for e in entries if not e.startswith('.')]
                
                for i, entry in enumerate(entries):
                    full_path = os.path.join(path, entry)
                    is_last = i == len(entries) - 1
                    current_prefix = "└── " if is_last else "├── "
                    items.append(prefix + current_prefix + entry)
                    
                    if os.path.isdir(full_path):
                        extension = "    " if is_last else "│   "
                        items.extend(get_tree_structure(full_path, prefix + extension, depth + 1))
                    elif not include_files:
                        continue
            except PermissionError:
                items.append(prefix + "└── [Permission Denied]")
            
            return items
        
        tree_lines = [dir_path]
        tree_lines.extend(get_tree_structure(dir_path))
        tree_output = '\n'.join(tree_lines)
        
        if args and args.dry_run:
            print_warning("DRY RUN: Would copy tree to clipboard (no changes made)")
            stats.skipped += 1
            return True

        # Format content with directory path and append to buffer
        formatted_content = f"===== DIRECTORY TREE: {dir_path} =====\n{tree_output}\n\n"
        stats.clipboard_buffer.append(formatted_content)
        print_success("TREE: Directory tree added to clipboard buffer.")
        stats.clipboard_dirs.append(dir_path)
        return True
