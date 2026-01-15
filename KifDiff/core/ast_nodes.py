"""AST (Abstract Syntax Tree) node definitions for KifDiff."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ASTNode:
    """Base class for all AST nodes."""
    line: int = 0
    column: int = 0


@dataclass
class Program(ASTNode):
    """Root node containing all directives."""
    directives: List['Directive'] = field(default_factory=list)


@dataclass
class Directive(ASTNode):
    """Base class for all directive nodes."""
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CreateDirective(Directive):
    """@Kif CREATE(<params>) <path>"""
    path: str = ""
    content: str = ""


@dataclass
class DeleteDirective(Directive):
    """@Kif DELETE(<params>) <path>"""
    path: str = ""


@dataclass
class MoveDirective(Directive):
    """@Kif MOVE(<params>) <source> <dest>"""
    source: str = ""
    dest: str = ""


@dataclass
class ReadDirective(Directive):
    """@Kif READ(<params>) <path>"""
    path: str = ""


@dataclass
class TreeDirective(Directive):
    """@Kif TREE(<params>) <path>"""
    path: str = ""


@dataclass
class OverwriteFileDirective(Directive):
    """@Kif OVERWRITE_FILE(<params>) <path>"""
    path: str = ""
    content: str = ""


@dataclass
class BeforeAfterBlock:
    """Represents a BEFORE/AFTER pair in SEARCH_AND_REPLACE."""
    before: str = ""
    after: str = ""


@dataclass
class SearchAndReplaceDirective(Directive):
    """@Kif SEARCH_AND_REPLACE(<params>) <path>
    
    Can contain multiple BEFORE/AFTER blocks.
    """
    path: str = ""
    blocks: List[BeforeAfterBlock] = field(default_factory=list)


@dataclass
class FindDirective(Directive):
    """@Kif FIND(<params>) <path>
    
    Parameters:
    - match_pattern: Regex pattern for file names to match
    - exclude: Regex pattern for files to exclude
    - include: Regex pattern for files to include
    """
    path: str = ""
