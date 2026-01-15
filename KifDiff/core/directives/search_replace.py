"""SEARCH_AND_REPLACE directive implementation."""

import os
import re
from difflib import get_close_matches
from utils.output import print_info, print_success, print_error, print_warning

class SearchReplaceDirective:
    """Handles @Kif SEARCH_AND_REPLACE directive."""
    
    def __init__(self):
        self._last_content = ""
    
    def normalize_whitespace(self, text):
        """Normalize whitespace by stripping trailing spaces from each line."""
        lines = text.split('\n')
        return '\n'.join(line.rstrip() for line in lines)

    def find_similar_content(self, content, search_text, threshold=0.6):
        """Find similar content blocks using fuzzy matching."""
        # Split content into chunks of similar size
        chunk_size = len(search_text)
        if chunk_size == 0:
            return []
        
        step = max(chunk_size // 4, 1)
        chunks = []
        positions = []
        
        for i in range(0, len(content) - chunk_size + 1, step):
            chunk = content[i:i+chunk_size]
            chunks.append(chunk)
            positions.append(i)
        
        matches = get_close_matches(search_text, chunks, n=3, cutoff=threshold)
        
        # Find positions and line numbers
        results = []
        for match in matches:
            try:
                idx = chunks.index(match)
                pos = positions[idx]
                line_num = content[:pos].count('\n') + 1
                results.append((line_num, match[:80]))
            except ValueError:
                continue
        
        return results

    def execute(self, file_path, blocks, params, stats, line_num=0, args=None):
        """Performs search and replace operations on a file.
        
        Args:
            file_path: Path to the file to modify
            blocks: List of BeforeAfterBlock objects or list of (before, after) tuples
            params: Parameters dict
            stats: Statistics object
            line_num: Line number for error reporting
            args: Command-line arguments
        """
        print_info(f"[Line {line_num}] SEARCH_AND_REPLACE: Modifying file '{file_path}'...")
        
        if not os.path.exists(file_path):
            print_error(f"ERROR: File '{file_path}' not found. Aborting operation.")
            stats.failed += 1
            return False

        # Get parameters
        replace_all = params.get('replace_all', False)
        count = params.get('count', 1)
        ignore_whitespace = params.get('ignore_whitespace', False)
        fuzzy_match = params.get('fuzzy_match', False)
        use_regex = params.get('regex', False)
        
        # If replace_all is true, count is ignored
        if replace_all:
            count = None
        
        if args and args.verbose:
            print(f"  Parameters: replace_all={replace_all}, count={count}, ignore_whitespace={ignore_whitespace}, regex={use_regex}")
            print(f"  Processing {len(blocks)} block(s)")

        # Convert blocks to uniform format
        normalized_blocks = []
        for block in blocks:
            if hasattr(block, 'before') and hasattr(block, 'after'):
                # It's a BeforeAfterBlock object
                normalized_blocks.append((block.before, block.after))
            elif isinstance(block, (tuple, list)) and len(block) == 2:
                # It's a tuple/list
                normalized_blocks.append((block[0], block[1]))
            else:
                print_error(f"ERROR: Invalid block format")
                stats.failed += 1
                return False

        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Process each block sequentially
            for block_idx, (before_text, after_text) in enumerate(normalized_blocks, 1):
                if args and args.verbose:
                    print(f"  Processing block {block_idx}/{len(normalized_blocks)}")
                
                success = self._process_single_block(
                    content, before_text, after_text, 
                    replace_all, count, ignore_whitespace, 
                    use_regex, file_path, args
                )
                
                if not success:
                    stats.failed += 1
                    return False
                
                # Update content for next block
                content = self._last_content
            
            # Backup and write the final content
            if args and not args.no_backup:
                from utils.backup import backup_file
                backup_file(file_path, args.backup_dir, args)
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            print_success(f"SEARCH_AND_REPLACE: Successfully processed {len(normalized_blocks)} block(s).")
            stats.modified += 1
            return True
            
        except IOError as e:
            print_error(f"ERROR: Could not modify file '{file_path}'. Reason: {e}")
            stats.failed += 1
            return False
    
    def _process_single_block(self, content, before_text, after_text, 
                              replace_all, count, ignore_whitespace, 
                              use_regex, file_path, args):
        """Process a single BEFORE/AFTER block.
        
        Returns True if successful, False otherwise.
        Stores the modified content in self._last_content.
        """

        # Normalize whitespace if requested
        search_before = self.normalize_whitespace(before_text) if ignore_whitespace else before_text
        search_content = self.normalize_whitespace(content) if ignore_whitespace else content

        # Check for matches
        matches_found = False
        match_count = 0
        match_positions = []
        
        if use_regex:
            try:
                pattern = re.compile(search_before, re.MULTILINE | re.DOTALL)
                matches = list(pattern.finditer(search_content))
                match_count = len(matches)
                matches_found = match_count > 0
                match_positions = [m.start() for m in matches]
                if args and args.verbose and matches_found:
                    print(f"    Regex pattern matched {match_count} occurrence(s)")
            except re.error as e:
                print_error(f"ERROR: Invalid regex pattern: {e}")
                return False
        else:
            matches_found = search_before in search_content
            match_count = search_content.count(search_before)
            if matches_found:
                match_positions = [i for i in range(len(search_content)) 
                                 if search_content.startswith(search_before, i)]

        if not matches_found:
            print_error(f"ERROR: 'BEFORE' block not found in '{file_path}'.")
            print("\n" + "="*60)
            print_warning("BEFORE block that wasn't found:")
            print("="*60)
            print(before_text)
            print("="*60 + "\n")
            
            # Show similar content
            similar = self.find_similar_content(content, before_text, threshold=0.6)
            if similar:
                print_info("Found similar content that might match:")
                for line_num_match, snippet in similar:
                    print(f"  Line {line_num_match}: {snippet}...")
            
            # Show first line matches
            before_lines = before_text.split('\n')
            first_line = before_lines[0].strip() if before_lines else ""
            if first_line and len(first_line) > 10:
                print_info(f"\nSearching for lines containing: '{first_line[:50]}'")
                found_matches = False
                for i, line in enumerate(content.split('\n'), 1):
                    if first_line[:20] in line:
                        print(f"  Line {i}: {line[:80]}")
                        found_matches = True
                if not found_matches:
                    print_warning("  No similar lines found.")
            
            return False

        if args and args.dry_run:
            print_warning("DRY RUN: Would modify file (no changes made)")
            print(f"  Found {match_count} occurrence(s)")
            if replace_all:
                print(f"  Would replace all {match_count} occurrence(s)")
            else:
                print("  Would replace first occurrence only")
            self._last_content = content
            return True
        
        if args and args.interactive:
            preview_start = match_positions[0]
            preview = content[max(0, preview_start-50):preview_start+len(before_text)+50]
            print("\nContext preview:")
            print("-" * 60)
            print(preview)
            print("-" * 60)
            response = input(f"Apply this change? (y/n): ")
            if response.lower() != 'y':
                print_warning("Skipped by user.")
                self._last_content = content
                return True

        # Perform replacement
        if use_regex:
            if replace_all:
                new_content = pattern.sub(after_text, content)
                if args and args.verbose:
                    print(f"    Replaced {match_count} occurrence(s) using regex")
            else:
                # Use count parameter (default 1)
                new_content = pattern.sub(after_text, content, count=count)
                if args and args.verbose:
                    print(f"    Replaced {count} occurrence(s) using regex")
        else:
            if replace_all:
                new_content = content.replace(before_text, after_text)
                if args and args.verbose:
                    print(f"    Replaced {match_count} occurrence(s)")
            else:
                # For literal text replacement, we need to handle count manually
                if count == 1:
                    new_content = content.replace(before_text, after_text, 1)
                else:
                    # Replace count occurrences manually
                    parts = []
                    remaining = content
                    replaced = 0
                    
                    while replaced < count and before_text in remaining:
                        index = remaining.find(before_text)
                        parts.append(remaining[:index])
                        parts.append(after_text)
                        remaining = remaining[index + len(before_text):]
                        replaced += 1
                    
                    parts.append(remaining)
                    new_content = ''.join(parts)
                
                if args and args.verbose:
                    print(f"    Replaced {count} occurrence(s)")

        self._last_content = new_content
        return True
