"""FIND directive implementation."""

import os
import re
from typing import List, Pattern
from utils.output import print_info, print_success, print_error, print_warning


class FindExecutor:
    """Handles @Kif FIND directive to find files matching patterns."""
    
    def compile_pattern(self, pattern_str: str) -> Pattern:
        """Compile a regex pattern string."""
        try:
            return re.compile(pattern_str)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern '{pattern_str}': {e}")
    
    def should_include_file(self, file_path: str, filename: str, 
                           match_pattern: Pattern, 
                           include_pattern: Pattern = None,
                           exclude_pattern: Pattern = None) -> bool:
        """Determine if a file should be included based on patterns."""
        # First check if it matches the main pattern
        if not match_pattern.search(filename):
            return False
        
        # Check exclude pattern
        if exclude_pattern and exclude_pattern.search(filename):
            return False
        
        # Check include pattern (if specified, must match)
        if include_pattern and not include_pattern.search(filename):
            return False
        
        return True
    
    def find_files(self, directory: str, match_pattern: Pattern,
                   include_pattern: Pattern = None,
                   exclude_pattern: Pattern = None,
                   max_depth: int = None) -> List[str]:
        """Recursively find files matching the patterns."""
        results = []
        
        def walk_directory(path: str, depth: int = 0):
            """Recursively walk directory."""
            if max_depth is not None and depth >= max_depth:
                return
            
            try:
                entries = os.listdir(path)
            except PermissionError:
                return
            
            for entry in sorted(entries):
                full_path = os.path.join(path, entry)
                
                if os.path.isfile(full_path):
                    if self.should_include_file(full_path, entry, match_pattern, 
                                              include_pattern, exclude_pattern):
                        results.append(full_path)
                elif os.path.isdir(full_path):
                    # Skip hidden directories unless explicitly included
                    if not entry.startswith('.'):
                        walk_directory(full_path, depth + 1)
        
        walk_directory(directory)
        return results
    
    def execute(self, directory: str, params: dict, stats, line_num: int = 0, args=None):
        """Execute FIND directive to find files matching patterns."""
        print_info(f"[Line {line_num}] FIND: Searching in '{directory}'...")
        
        if not os.path.exists(directory):
            error_msg = f"ERROR: Directory '{directory}' not found."
            print_error(error_msg)
            stats.failed += 1
            return False
        
        if not os.path.isdir(directory):
            error_msg = f"ERROR: '{directory}' is not a directory."
            print_error(error_msg)
            stats.failed += 1
            return False
        
        # Get parameters
        match_pattern_str = params.get('match_pattern', params.get('pattern', '.*'))
        include_pattern_str = params.get('include', None)
        exclude_pattern_str = params.get('exclude', None)
        max_depth = params.get('depth', None)
        
        if args and args.verbose:
            print(f"  Parameters:")
            print(f"    match_pattern: {match_pattern_str}")
            if include_pattern_str:
                print(f"    include: {include_pattern_str}")
            if exclude_pattern_str:
                print(f"    exclude: {exclude_pattern_str}")
            if max_depth:
                print(f"    depth: {max_depth}")
        
        # Compile patterns
        try:
            match_pattern = self.compile_pattern(match_pattern_str)
            include_pattern = self.compile_pattern(include_pattern_str) if include_pattern_str else None
            exclude_pattern = self.compile_pattern(exclude_pattern_str) if exclude_pattern_str else None
        except ValueError as e:
            print_error(f"ERROR: {e}")
            stats.failed += 1
            return False
        
        if args and args.dry_run:
            print_warning("DRY RUN: Would search for files (no changes made)")
            stats.skipped += 1
            return True
        
        # Find files
        try:
            files = self.find_files(directory, match_pattern, include_pattern, 
                                   exclude_pattern, max_depth)
            
            if not files:
                print_warning(f"No files found matching the criteria in '{directory}'")
                return True
            
            # Print results
            print_success(f"FIND: Found {len(files)} file(s):")
            for file_path in files:
                # Print relative path if possible
                try:
                    rel_path = os.path.relpath(file_path, directory)
                    print(f"  - {rel_path}")
                except ValueError:
                    # If relative path fails, print absolute
                    print(f"  - {file_path}")
            
            # Add results to clipboard
            formatted_content = f"===== FIND RESULTS: {directory} =====\n"
            formatted_content += f"Match Pattern: {match_pattern_str}\n"
            if include_pattern_str:
                formatted_content += f"Include: {include_pattern_str}\n"
            if exclude_pattern_str:
                formatted_content += f"Exclude: {exclude_pattern_str}\n"
            formatted_content += f"\nFound {len(files)} file(s):\n"
            for file_path in files:
                try:
                    rel_path = os.path.relpath(file_path, directory)
                    formatted_content += f"  - {rel_path}\n"
                except ValueError:
                    formatted_content += f"  - {file_path}\n"
            formatted_content += "\n"
            
            stats.clipboard_buffer.append(formatted_content)
            stats.clipboard_dirs.append(directory)
            
            return True
            
        except Exception as e:
            error_msg = f"ERROR: Failed to search directory: {e}"
            print_error(error_msg)
            stats.failed += 1
            return False
