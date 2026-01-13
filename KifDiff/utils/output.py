"""Output utilities for KifDiff with color support."""

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
