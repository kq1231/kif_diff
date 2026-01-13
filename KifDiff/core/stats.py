"""Statistics tracking for KifDiff operations."""

class Stats:
    """Track statistics of operations."""
    def __init__(self):
        self.created = 0
        self.deleted = 0
        self.modified = 0
        self.failed = 0
        self.skipped = 0
        self.clipboard_files = []  # Track files copied to clipboard
        self.clipboard_dirs = []   # Track directories copied to clipboard
        self.clipboard_errors = []  # Track errors copied to clipboard
    
    def print_summary(self):
        """Print operation summary."""
        from utils.output import print_info, print_success, print_error
        
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
