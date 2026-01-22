"""Core module for KifDiff."""

from .stats import Stats
from .kifdiff import validate_kifdiff, process_diff_files
from .parser import parse_kifdiff

__all__ = ['Stats', 'validate_kifdiff', 'process_diff_files', 'parse_kifdiff']