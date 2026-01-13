#!/usr/bin/env python3
import os
import sys
import argparse
import re
from difflib import get_close_matches
from datetime import datetime
import json

# Color output support
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    COLOR_SUPPORT = True
except ImportError:
    COLOR_SUPPORT = False
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = BLUE = ""
    class Style:
        RESET_ALL = BRIGHT = ""

def print_success(msg):
    """Print success message in green."""
    if COLOR_SUPPORT:
        print(f"{Fore.GREEN}{msg}{Style.RESET_ALL}")
    else:
        print(msg)

def print_error(msg):
    """Print error message in red."""
    if COLOR_SUPPORT:
        print(f"{Fore.RED}{msg}{Style.RESET_ALL}")
    else:
        print(msg)

def print_warning(msg):
    """Print warning message in yellow."""
    if COLOR_SUPPORT:
        print(f"{Fore.YELLOW}{msg}{Style.RESET_ALL}")
    else:
        print(msg)

def print_info(msg):
    """Print info message in cyan."""
    if COLOR_SUPPORT:
        print(f"{Fore.CYAN}{msg}{Style.RESET_ALL}")
    else:
        print(msg)

def print_tree(msg):
    """Print tree output in blue."""
    if COLOR_SUPPORT:
        print(f"{Fore.BLUE}{msg}{Style.RESET_ALL}")
    else:
        print(msg)

class Stats:
    """Track statistics of operations."""
    def __init__(self):
        self.created = 0
        self.deleted = 0
        self.modified = 0
        self.failed = 0
        self.skipped = 0
    
    def print_summary(self):
        """Print operation summary."""
        print("\n" + "="*50)
        print_info("SUMMARY")
        print("="*50)
        print(f"Files created:  {self.created}")
        print(f"Files deleted:  {self.deleted}")
        print(f"Files modified: {self.modified}")
        print(f"Files skipped:  {self.skipped}")
        if self.failed > 0:
            print_error(f"Operations failed: {self.failed}")
        else:
            print_success("All operations completed successfully!")
        print("="*50)

class DirectiveParams:
    """Parse and store directive parameters."""
    def __init__(self, param_string=""):
        self.params = {}
        if param_string:
            self._parse(param_string)
    
    def _parse(self, param_string):
        """Parse parameter string like 'replace_all=true, ignore_whitespace=false'"""
        # Remove parentheses if present
        param_string = param_string.strip('()')
        if not param_string:
            return
        
        # Split by comma
        for param in param_string.split(','):
            param = param.strip()
            if '=' in param:
                key, value = param.split('=', 1)
                key = key.strip()
                value = value.strip().lower()
                
                # Convert string values to appropriate types
                if value == 'true':
                    self.params[key] = True
                elif value == 'false':
                    self.params[key] = False
                elif value.isdigit():
                    self.params[key] = int(value)
                else:
                    self.params[key] = value
    
    def get(self, key, default=None):
        """Get parameter value with default."""
        return self.params.get(key, default)

def backup_file(file_path, backup_dir=".kif_backups"):
    """Creates a backup of the file in a dedicated folder for this session."""
    if not os.path.exists(file_path):
        return None
    
    # Create session-specific backup directory with timestamp
    session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(backup_dir, f"session_{session_timestamp}")
    
    # Use global session_backup_dir if it exists, otherwise create new one
    global session_backup_dir
    if 'session_backup_dir' not in globals():
        session_backup_dir = session_dir
    
    os.makedirs(session_backup_dir, exist_ok=True)
    
    # Preserve directory structure in backup
    # Convert absolute path to relative and sanitize
    if os.path.isabs(file_path):
        # Remove leading slash/drive letter to make it relative
        rel_path = file_path.lstrip(os.sep)
        if os.name == 'nt' and len(rel_path) > 1 and rel_path[1] == ':':
            rel_path = rel_path[0] + rel_path[2:]  # Remove colon from drive letter
    else:
        rel_path = file_path
    
    backup_file_path = os.path.join(session_backup_dir, rel_path)
    backup_file_dir = os.path.dirname(backup_file_path)
    
    try:
        # Create directory structure
        os.makedirs(backup_file_dir, exist_ok=True)
        
        # If backup file already exists in this session, append counter
        if os.path.exists(backup_file_path):
            base, ext = os.path.splitext(backup_file_path)
            counter = 1
            while os.path.exists(f"{base}.{counter}{ext}"):
                counter += 1
            backup_file_path = f"{base}.{counter}{ext}"
        
        # Copy file
        with open(file_path, 'r') as src, open(backup_file_path, 'w') as dst:
            dst.write(src.read())
        
        if args.verbose:
            print_info(f"Backup created: {backup_file_path}")
        
        # Update backup manifest
        manifest_path = os.path.join(session_backup_dir, "manifest.json")
        manifest = {}
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
        
        if file_path not in manifest:
            manifest[file_path] = []
        manifest[file_path].append({
            "backup": backup_file_path,
            "timestamp": session_timestamp,
            "session": session_backup_dir
        })
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return backup_file_path
    except IOError as e:
        print_error(f"Could not create backup: {e}")
        return None

def create_file(file_path, content, stats, line_num=0):
    """Creates a file with the given content."""
    print_info(f"[Line {line_num}] CREATE: Creating file '{file_path}'...")
    
    if args.dry_run:
        print_warning("DRY RUN: Would create file (no changes made)")
        print(f"Content preview: {content[:100]}..." if len(content) > 100 else content)
        stats.skipped += 1
        return
    
    if args.interactive:
        response = input(f"Create file '{file_path}'? (y/n): ")
        if response.lower() != 'y':
            print_warning("Skipped by user.")
            stats.skipped += 1
            return
    
    try:
        os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)
        print_success("CREATE: Success.")
        stats.created += 1
    except IOError as e:
        print_error(f"ERROR: Could not create file '{file_path}'. Reason: {e}")
        stats.failed += 1

def delete_file(file_path, stats, line_num=0):
    """Deletes the specified file."""
    print_info(f"[Line {line_num}] DELETE: Deleting file '{file_path}'...")
    
    if not os.path.exists(file_path):
        print_warning(f"WARNING: File '{file_path}' not found. Skipping.")
        stats.skipped += 1
        return
    
    if args.dry_run:
        print_warning("DRY RUN: Would delete file (no changes made)")
        stats.skipped += 1
        return
    
    if args.interactive:
        response = input(f"Delete file '{file_path}'? (y/n): ")
        if response.lower() != 'y':
            print_warning("Skipped by user.")
            stats.skipped += 1
            return
    
    # Backup before deleting
    if not args.no_backup:
        backup_file(file_path)
    
    try:
        os.remove(file_path)
        print_success("DELETE: Success.")
        stats.deleted += 1
    except OSError as e:
        print_error(f"ERROR: Could not delete file '{file_path}'. Reason: {e}")
        stats.failed += 1

def normalize_whitespace(text):
    """Normalize whitespace by stripping trailing spaces from each line."""
    lines = text.split('\n')
    return '\n'.join(line.rstrip() for line in lines)

def find_similar_content(content, search_text, threshold=0.6):
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

def search_and_replace(file_path, before_text, after_text, params, stats, line_num=0):
    """Performs a search and replace operation on a file."""
    print_info(f"[Line {line_num}] SEARCH_AND_REPLACE: Modifying file '{file_path}'...")
    
    if not os.path.exists(file_path):
        print_error(f"ERROR: File '{file_path}' not found. Aborting operation.")
        stats.failed += 1
        return

    # Get parameters
    replace_all = params.get('replace_all', False)
    count = params.get('count', 1)
    ignore_whitespace = params.get('ignore_whitespace', False)
    fuzzy_match = params.get('fuzzy_match', False)
    use_regex = params.get('regex', False)
    
    # If replace_all is true, count is ignored
    if replace_all:
        count = None
    
    if args.verbose:
        print(f"  Parameters: replace_all={replace_all}, count={count}, ignore_whitespace={ignore_whitespace}, regex={use_regex}")

    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Normalize whitespace if requested
        search_before = normalize_whitespace(before_text) if ignore_whitespace else before_text
        search_content = normalize_whitespace(content) if ignore_whitespace else content

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
                if args.verbose and matches_found:
                    print(f"  Regex pattern matched {match_count} occurrence(s)")
            except re.error as e:
                print_error(f"ERROR: Invalid regex pattern: {e}")
                stats.failed += 1
                return
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
            similar = find_similar_content(content, before_text, threshold=0.6)
            if similar:
                print_info("Found similar content that might match:")
                for line_num_match, snippet in similar:
                    print(f"  Line {line_num_match}: {snippet}...")
            
            # Show first line matches
            before_lines = before_text.split('\n')
            first_line = before_lines[0].strip() if before_lines else ""
            if first_line and len(first_line) > 10:
                print_info(f"\nSearching for lines containing: '{first_line[:50]}'")
                matches_found = False
                for i, line in enumerate(content.split('\n'), 1):
                    if first_line[:20] in line:
                        print(f"  Line {i}: {line[:80]}")
                        matches_found = True
                if not matches_found:
                    print_warning("  No similar lines found.")
            
            stats.failed += 1
            return

        if args.dry_run:
            print_warning("DRY RUN: Would modify file (no changes made)")
            print(f"  Found {match_count} occurrence(s)")
            if replace_all:
                print(f"  Would replace all {match_count} occurrence(s)")
            else:
                print("  Would replace first occurrence only")
            stats.skipped += 1
            return
        
        if args.interactive:
            preview_start = match_positions[0]
            preview = content[max(0, preview_start-50):preview_start+len(before_text)+50]
            print("\nContext preview:")
            print("-" * 60)
            print(preview)
            print("-" * 60)
            response = input(f"Apply this change? (y/n): ")
            if response.lower() != 'y':
                print_warning("Skipped by user.")
                stats.skipped += 1
                return

        # Backup before modifying
        if not args.no_backup:
            backup_file(file_path)

        # Perform replacement
        if use_regex:
            if replace_all:
                new_content = pattern.sub(after_text, content)
                if args.verbose:
                    print(f"  Replaced {match_count} occurrence(s) using regex")
            else:
                # Use count parameter (default 1)
                new_content = pattern.sub(after_text, content, count=count)
                if args.verbose:
                    print(f"  Replaced {count} occurrence(s) using regex")
        else:
            if replace_all:
                new_content = content.replace(before_text, after_text)
                if args.verbose:
                    print(f"  Replaced {match_count} occurrence(s)")
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
                
                if args.verbose:
                    print(f"  Replaced {count} occurrence(s)")

        with open(file_path, 'w') as f:
            f.write(new_content)
        print_success("SEARCH_AND_REPLACE: Success.")
        stats.modified += 1
    except IOError as e:
        print_error(f"ERROR: Could not modify file '{file_path}'. Reason: {e}")
        stats.failed += 1

def list_backup_sessions(backup_dir=".kif_backups"):
    """List all backup sessions."""
    if not os.path.exists(backup_dir):
        print_error("No backup directory found.")
        return []
    
    sessions = []
    for item in os.listdir(backup_dir):
        item_path = os.path.join(backup_dir, item)
        if os.path.isdir(item_path) and item.startswith("session_"):
            manifest_path = os.path.join(item_path, "manifest.json")
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                sessions.append({
                    "path": item_path,
                    "name": item,
                    "files": len(manifest)
                })
    
    # Sort by timestamp (newest first)
    sessions.sort(key=lambda x: x["name"], reverse=True)
    return sessions

def read_file_to_clipboard(file_path, stats, line_num=0):
    """Reads a file and copies its contents with file path to clipboard."""
    print_info(f"[Line {line_num}] READ: Reading file '{file_path}'...")
    
    if not os.path.exists(file_path):
        print_error(f"ERROR: File '{file_path}' not found. Skipping.")
        stats.failed += 1
        return
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Try to import pyperclip for clipboard operations
        try:
            import pyperclip
            
            # Format content with file path
            formatted_content = f"===== FILE: {file_path} =====\n{content}\n\n"
            
            # Check if we already have content in clipboard
            try:
                existing_content = pyperclip.paste()
                # Only append if the existing content doesn't already include this file
                if existing_content and file_path not in existing_content:
                    new_content = existing_content + formatted_content
                else:
                    new_content = formatted_content
            except:
                new_content = formatted_content
            
            # Copy to clipboard
            pyperclip.copy(new_content)
            print_success(f"READ: File content copied to clipboard.")
            stats.modified += 1
        except ImportError:
            print_error("ERROR: pyperclip module not installed. Install it with 'pip install pyperclip'")
            print("Falling back to printing file content:")
            print("\n" + "="*60)
            print(f"FILE: {file_path}")
            print("="*60)
            print(content)
            print("="*60 + "\n")
            stats.modified += 1
            
    except IOError as e:
        print_error(f"ERROR: Could not read file '{file_path}'. Reason: {e}")
        stats.failed += 1

def show_directory_tree(dir_path, params, stats, line_num=0):
    """Displays directory tree structure and copies it to clipboard."""
    print_info(f"[Line {line_num}] TREE: Showing tree for '{dir_path}'...")
    
    if not os.path.exists(dir_path):
        print_error(f"ERROR: Directory '{dir_path}' not found. Skipping.")
        stats.failed += 1
        return
    
    if not os.path.isdir(dir_path):
        print_error(f"ERROR: '{dir_path}' is not a directory. Skipping.")
        stats.failed += 1
        return
    
    # Get parameters
    max_depth = params.get('depth', None)
    show_hidden = params.get('show_hidden', False)
    include_files = params.get('include_files', True)
    
    if args.verbose:
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
    
    if args.dry_run:
        print_warning("DRY RUN: Would copy tree to clipboard (no changes made)")
        stats.skipped += 1
        return
    
    # Try to import pyperclip for clipboard operations
    try:
        import pyperclip
        
        # Format content with directory path
        formatted_content = f"===== DIRECTORY TREE: {dir_path} =====\n{tree_output}\n\n"
        
        # Check if we already have content in clipboard
        try:
            existing_content = pyperclip.paste()
            # Only append if the existing content doesn't already include this directory
            if existing_content and dir_path not in existing_content:
                new_content = existing_content + formatted_content
            else:
                new_content = formatted_content
        except:
            new_content = formatted_content
        
        # Copy to clipboard
        pyperclip.copy(new_content)
        print_success(f"TREE: Directory tree copied to clipboard.")
        stats.modified += 1
    except ImportError:
        print_error("ERROR: pyperclip module not installed. Install it with 'pip install pyperclip'")
        print("Falling back to printing tree structure:")
        print("\n" + "="*60)
        print_tree("DIRECTORY TREE")
        print("="*60)
        for line in tree_lines:
            print_tree(line)
        print("="*60 + "\n")
        stats.modified += 1

def rollback_backups(backup_dir=".kif_backups", session_name=None):
    """Restore all files from backups."""
    
    # If no session specified, use most recent
    if session_name is None:
        sessions = list_backup_sessions(backup_dir)
        if not sessions:
            print_error("No backup sessions found.")
            return
        
        print_info(f"Found {len(sessions)} backup session(s):")
        for i, session in enumerate(sessions, 1):
            print(f"  {i}. {session['name']} ({session['files']} file(s))")
        
        # Use most recent session
        session_dir = sessions[0]["path"]
        print_info(f"\nUsing most recent session: {sessions[0]['name']}")
    else:
        session_dir = os.path.join(backup_dir, session_name)
        if not os.path.exists(session_dir):
            print_error(f"Session not found: {session_name}")
            return
    
    manifest_path = os.path.join(session_dir, "manifest.json")
    
    if not os.path.exists(manifest_path):
        print_error("No backup manifest found in session.")
        return
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    print_info(f"Restoring {len(manifest)} file(s)...")
    
    restored = 0
    failed = 0
    
    for original_path, backups in manifest.items():
        if not backups:
            continue
        
        # Get most recent backup
        latest_backup = backups[-1]["backup"]
        
        if not os.path.exists(latest_backup):
            print_warning(f"Backup not found: {latest_backup}")
            failed += 1
            continue
        
        try:
            with open(latest_backup, 'r') as src:
                content = src.read()
            
            os.makedirs(os.path.dirname(original_path) or '.', exist_ok=True)
            with open(original_path, 'w') as dst:
                dst.write(content)
            
            print_success(f"Restored: {original_path}")
            restored += 1
        except IOError as e:
            print_error(f"Could not restore {original_path}: {e}")
            failed += 1
    
    print("\n" + "="*50)
    print_success(f"Successfully restored {restored} file(s)")
    if failed > 0:
        print_error(f"Failed to restore {failed} file(s)")
    print("="*50)

def validate_kifdiff(file_path):
    """Validate that all operations can be performed without executing them."""
    print_info(f"Validating KifDiff file: {file_path}")
    
    global args
    original_dry_run = args.dry_run
    args.dry_run = True
    
    stats = Stats()
    parse_kifdiff(file_path, stats)
    
    args.dry_run = original_dry_run
    
    if stats.failed == 0:
        print_success("\n✓ Validation passed! All operations can be performed.")
        return True
    else:
        print_error(f"\n✗ Validation failed! {stats.failed} operation(s) would fail.")
        return False

def parse_kifdiff(file_path, stats=None):
    """Parses and executes a .kifdiff file."""
    if stats is None:
        stats = Stats()
    
    # Initialize session backup directory for this run
    global session_backup_dir
    session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_backup_dir = os.path.join(args.backup_dir, f"session_{session_timestamp}")
    
    print_info(f"--- Processing KifDiff file: {file_path} ---")
    if not args.no_backup:
        print_info(f"Backup session: {session_backup_dir}")
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print_error(f"FATAL ERROR: KifDiff file '{file_path}' not found.")
        stats.failed += 1
        return stats

    current_file = None
    mode = None
    buffer = []
    current_params = DirectiveParams()
    directive_line = 0

    for i, line in enumerate(lines, 1):
        stripped_line = line.strip()

        if stripped_line.startswith("@Kif FILE"):
            current_file = stripped_line.split(" ", 2)[2]
            if args.verbose:
                print(f"\n[Line {i}] Target file: {current_file}")
            continue

        # Check if this line needs a file context
        needs_file_context = any(stripped_line.startswith(d) for d in [
            "@Kif CREATE", "@Kif DELETE", "@Kif SEARCH_AND_REPLACE"
        ])
        
        if needs_file_context and not current_file:
            print_warning(f"WARNING: No file specified before an operation at line {i}. Skipping.")
            continue

        # Mode Switches with parameters
        if stripped_line.startswith("@Kif CREATE"):
            mode = "CREATE"
            buffer = []
            directive_line = i
            # Extract parameters if present
            match = re.search(r'@Kif CREATE\((.*?)\)', stripped_line)
            if match:
                current_params = DirectiveParams(match.group(1))
            else:
                current_params = DirectiveParams()
            continue
        elif stripped_line == "@Kif END_CREATE":
            if mode == "CREATE":
                create_file(current_file, "".join(buffer), stats, directive_line)
                mode = None
            continue

        if stripped_line.startswith("@Kif DELETE"):
            directive_line = i
            delete_file(current_file, stats, directive_line)
            continue
            
        if stripped_line.startswith("@Kif READ"):
            # Extract file path from READ directive
            read_file_path = stripped_line.split(" ", 2)[2] if len(stripped_line.split(" ", 2)) > 2 else ""
            if not read_file_path:
                print_error(f"ERROR: No file path specified for READ directive at line {i}.")
                stats.failed += 1
                continue
            directive_line = i
            read_file_to_clipboard(read_file_path, stats, directive_line)
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
            show_directory_tree(tree_dir, current_params, stats, directive_line)
            continue
        elif stripped_line == "@Kif END_SEARCH_AND_REPLACE":
            if mode == "SEARCH_AND_REPLACE":
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
                    
                    search_and_replace(current_file, before_text, after_text, current_params, stats, directive_line)
                except (ValueError, IndexError) as e:
                    print_error(f"ERROR: Malformed SEARCH_AND_REPLACE block for file '{current_file}' at line {directive_line}.")
                    if args.verbose:
                        print(f"  Details: {e}")
                    stats.failed += 1
                mode = None
            continue

        # Buffer content
        if mode:
            buffer.append(line)

    print_info("\n--- KifDiff processing complete. ---")
    stats.print_summary()
    return stats

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="KifDiff: A powerful file modification tool with safety features.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s changes.kifdiff                    # Apply changes
  %(prog)s changes.kifdiff --dry-run          # Preview changes
  %(prog)s changes.kifdiff --validate         # Validate without applying
  %(prog)s changes.kifdiff -i                 # Interactive mode
  %(prog)s --rollback                         # Undo last changes
  %(prog)s --list-sessions                    # List all backup sessions
  %(prog)s --rollback-session session_XXX     # Restore specific session
  %(prog)s file1.kifdiff file2.kifdiff        # Apply multiple files

Directives:
  @Kif FILE <path>                            # Set target file for operations
  @Kif CREATE                                 # Create a new file
  @Kif DELETE                                 # Delete the target file
  @Kif READ <path>                            # Read file content to clipboard
  @Kif TREE <dir>                             # Copy directory tree structure to clipboard
  @Kif SEARCH_AND_REPLACE                     # Replace content in file

Directive Parameters:
  @Kif SEARCH_AND_REPLACE(replace_all=true, ignore_whitespace=false)
  @Kif TREE(depth=3, show_hidden=false, include_files=true)
  
  Available parameters for SEARCH_AND_REPLACE:
    - replace_all: Replace all occurrences (default: false)
    - ignore_whitespace: Ignore trailing whitespace (default: false)
    - fuzzy_match: Use fuzzy matching (default: false)
    - regex: Use regular expressions (default: false)
    - count: Number of replacements (default: 1)
  
  Available parameters for TREE:
    - depth: Maximum depth to display (default: unlimited)
    - show_hidden: Show hidden files/directories (default: false)
    - include_files: Show files in tree (default: true)
    - Note: Tree structure is copied to clipboard, not displayed
        """
    )

    
    # Positional arguments
    parser.add_argument("diff_file", nargs='*', 
                       help="One or more .kifdiff files to apply")
    
    # Safety features
    parser.add_argument("--dry-run", action="store_true",
                       help="Preview changes without modifying files")
    parser.add_argument("--validate", action="store_true",
                       help="Validate all operations can be performed")
    parser.add_argument("-i", "--interactive", action="store_true",
                       help="Ask for confirmation before each operation")
    parser.add_argument("--no-backup", action="store_true",
                       help="Skip creating backup files")
    
    # Utility features
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Show detailed information during processing")
    parser.add_argument("--rollback", action="store_true",
                       help="Restore files from most recent backups")
    parser.add_argument("--list-sessions", action="store_true",
                       help="List all backup sessions")
    parser.add_argument("--rollback-session",
                       help="Restore files from a specific backup session")
    parser.add_argument("--backup-dir", default=".kif_backups",
                       help="Directory for backup files (default: .kif_backups)")
    
    # Git integration
    parser.add_argument("--git-commit", action="store_true",
                       help="Automatically commit changes to git after applying")
    parser.add_argument("--git-message", default="Applied KifDiff changes",
                       help="Git commit message (default: 'Applied KifDiff changes')")
    
    args = parser.parse_args()
    
    # Handle list sessions
    if args.list_sessions:
        sessions = list_backup_sessions(args.backup_dir)
        if not sessions:
            print_error("No backup sessions found.")
            sys.exit(1)
        
        print_info("Available backup sessions:")
        for i, session in enumerate(sessions, 1):
            print(f"  {i}. {session['name']} ({session['files']} file(s))")
        print(f"\nTo restore a session, use: --rollback-session {sessions[0]['name']}")
        sys.exit(0)
    
    # Handle rollback
    if args.rollback:
        rollback_backups(args.backup_dir)
        sys.exit(0)
    
    # Handle specific session rollback
    if args.rollback_session:
        rollback_backups(args.backup_dir, args.rollback_session)
        sys.exit(0)
    
    # Require at least one diff file
    if not args.diff_file:
        parser.print_help()
        sys.exit(1)
    
    # Validate all files exist
    for diff_file in args.diff_file:
        if not os.path.exists(diff_file):
            print_error(f"FATAL ERROR: The specified .kifdiff file '{diff_file}' does not exist.")
            sys.exit(1)
    
    # Validation mode
    if args.validate:
        all_valid = True
        for diff_file in args.diff_file:
            if not validate_kifdiff(diff_file):
                all_valid = False
        sys.exit(0 if all_valid else 1)
    
    # Process all diff files
    total_stats = Stats()
    for diff_file in args.diff_file:
        if len(args.diff_file) > 1:
            print(f"\n{'='*60}")
            print_info(f"Processing: {diff_file}")
            print(f"{'='*60}\n")
        
        stats = parse_kifdiff(diff_file)
        
        # Aggregate stats
        total_stats.created += stats.created
        total_stats.deleted += stats.deleted
        total_stats.modified += stats.modified
        total_stats.failed += stats.failed
        total_stats.skipped += stats.skipped
    
    # Print total stats if multiple files
    if len(args.diff_file) > 1:
        print(f"\n{'='*60}")
        print_info("TOTAL SUMMARY FOR ALL FILES")
        print(f"{'='*60}")
        total_stats.print_summary()
    
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
    
    # Exit with appropriate code
    sys.exit(0 if total_stats.failed == 0 else 1)