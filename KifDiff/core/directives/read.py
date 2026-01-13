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
            
            # Copy error to clipboard
            try:
                import pyperclip
                formatted_error = f"===== READ ERROR: {file_path} =====\n{error_msg}\n\n"
                
                # Copy to clipboard (replace, not append)
                pyperclip.copy(formatted_error)
                print_warning("READ: Error message copied to clipboard.")
                stats.clipboard_errors.append(f"READ: {file_path}")
            except ImportError:
                pass  # Silently ignore if pyperclip not available for errors
            return False
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Try to import pyperclip for clipboard operations
            try:
                import pyperclip
                
                # Format content with file path
                formatted_content = f"===== FILE: {file_path} =====\n{content}\n\n"
                
                # Copy to clipboard (replace, not append)
                pyperclip.copy(formatted_content)
                print_success("READ: File content copied to clipboard.")
                stats.clipboard_files.append(file_path)
                stats.modified += 1
                return True
            except ImportError:
                print_error("ERROR: pyperclip module not installed. Install it with 'pip install pyperclip'")
                print("Falling back to printing file content:")
                print("\n" + "="*60)
                print(f"FILE: {file_path}")
                print("="*60)
                print(content)
                print("="*60 + "\n")
                stats.modified += 1
                return True
                
        except IOError as e:
            error_msg = f"ERROR: Could not read file '{file_path}'. Reason: {e}"
            print_error(error_msg)
            stats.failed += 1
            
            # Copy error to clipboard
            try:
                import pyperclip
                formatted_error = f"===== READ ERROR: {file_path} =====\n{error_msg}\n\n"
                
                # Copy to clipboard (replace, not append)
                pyperclip.copy(formatted_error)
                print_warning("READ: Error message copied to clipboard.")
                stats.clipboard_errors.append(f"READ: {file_path}")
            except ImportError:
                pass  # Silently ignore if pyperclip not available for errors
            return False
