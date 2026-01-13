"""FILE directive implementation."""

class FileDirective:
    """Handles @Kif FILE directive to set target file."""
    
    def __init__(self):
        self.current_file = None
    
    def execute(self, file_path, stats, args=None):
        """Set the current target file."""
        self.current_file = file_path
        if args and args.verbose:
            print(f"\nTarget file: {file_path}")
        return True
    
    def get_current_file(self):
        """Get the current target file."""
        return self.current_file
