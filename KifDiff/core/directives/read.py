"""READ directive implementation."""

import os
from utils.output import print_info, print_success, print_error, print_warning

class ReadDirective:
    """Handles @Kif READ directive to read files to clipboard."""
    
    def execute(self, file_path, stats, line_num=0, args=None):
        """Reads a file and copies its contents with file path to clipboard."""
        print_info(f"[Line {line_num}] READ: Reading file '{file_path}'...")
        
        if not os.path.exists(file_path):
            error_msg = f"ERROR: File '{file_path}' not found. Skipping."
            print_error(error_msg)
            stats.failed += 1

            # Append error to clipboard buffer
            formatted_error = f"===== READ ERROR: {file_path} =====\n{error_msg}\n\n"
            stats.clipboard_buffer.append(formatted_error)
            stats.clipboard_errors.append(f"READ: {file_path}")
            return False
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Format content with file path and append to buffer
            formatted_content = f"===== FILE: {file_path} =====\n{content}\n\n"
            stats.clipboard_buffer.append(formatted_content)
            print_success("READ: File content added to clipboard buffer.")
            stats.clipboard_files.append(file_path)
            stats.modified += 1
            return True

        except IOError as e:
            error_msg = f"ERROR: Could not read file '{file_path}'. Reason: {e}"
            print_error(error_msg)
            stats.failed += 1

            # Append error to clipboard buffer
            formatted_error = f"===== READ ERROR: {file_path} =====\n{error_msg}\n\n"
            stats.clipboard_buffer.append(formatted_error)
            stats.clipboard_errors.append(f"READ: {file_path}")
            return False
