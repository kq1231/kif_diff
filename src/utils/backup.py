"""Backup functionality for KifDiff."""

import os
import json
from datetime import datetime

def backup_file(file_path, backup_dir=".kif_backups", args=None):
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
        
        if args and args.verbose:
            from .output import print_info
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
        from .output import print_error
        print_error(f"Could not create backup: {e}")
        return None

def list_backup_sessions(backup_dir=".kif_backups"):
    """List all backup sessions."""
    if not os.path.exists(backup_dir):
        from .output import print_error
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

def rollback_backups(backup_dir=".kif_backups", session_name=None):
    """Restore all files from backups."""
    from .output import print_info, print_success, print_error
    
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
