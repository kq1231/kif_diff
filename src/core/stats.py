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
        self.clipboard_buffer = []  # Accumulate all clipboard content
    
    def print_summary(self):
        """Print operation summary with beautiful formatting."""
        from utils.output import print_summary_table
        print_summary_table(self)
