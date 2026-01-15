"""Lexer for KifDiff - Tokenizes input into a stream of tokens."""

import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional


class TokenType(Enum):
    """Token types for KifDiff syntax."""
    # Directive marker
    DIRECTIVE_START = auto()  # @Kif
    
    # Directive names
    CREATE = auto()
    DELETE = auto()
    MOVE = auto()
    READ = auto()
    TREE = auto()
    SEARCH_AND_REPLACE = auto()
    OVERWRITE_FILE = auto()
    FIND = auto()
    
    # Block markers
    BEFORE = auto()
    END_BEFORE = auto()
    AFTER = auto()
    END_AFTER = auto()
    END_CREATE = auto()
    END_OVERWRITE_FILE = auto()
    END_SEARCH_AND_REPLACE = auto()
    
    # Syntax elements
    LPAREN = auto()  # (
    RPAREN = auto()  # )
    COMMA = auto()   # ,
    EQUALS = auto()  # =
    
    # Values
    IDENTIFIER = auto()  # Parameter names, boolean values, etc.
    NUMBER = auto()
    STRING = auto()
    PATH = auto()  # File/directory paths
    
    # Content
    CONTENT = auto()  # Text content in blocks
    
    # Special
    NEWLINE = auto()
    EOF = auto()


@dataclass
class Token:
    """Represents a token in the input stream."""
    type: TokenType
    value: str
    line: int
    column: int
    
    def __repr__(self):
        return f"Token({self.type.name}, {repr(self.value)}, L{self.line}:{self.column})"


class Lexer:
    """Tokenizes KifDiff syntax into a stream of tokens."""
    
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        
    def error(self, msg: str):
        """Raise a lexer error."""
        raise SyntaxError(f"Lexer error at line {self.line}, column {self.column}: {msg}")
    
    def peek(self, offset: int = 0) -> Optional[str]:
        """Peek at character at current position + offset."""
        pos = self.pos + offset
        if pos < len(self.text):
            return self.text[pos]
        return None
    
    def advance(self) -> Optional[str]:
        """Advance position and return current character."""
        if self.pos >= len(self.text):
            return None
        
        char = self.text[self.pos]
        self.pos += 1
        
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        
        return char
    
    def skip_whitespace(self, skip_newlines: bool = False):
        """Skip whitespace characters."""
        while self.peek():
            char = self.peek()
            if char == '\n' and not skip_newlines:
                break
            if char in ' \t\r' or (char == '\n' and skip_newlines):
                self.advance()
            else:
                break
    
    def read_until_newline(self) -> str:
        """Read until end of line."""
        result = []
        while self.peek() and self.peek() != '\n':
            result.append(self.advance())
        return ''.join(result)
    
    def read_directive_name(self) -> str:
        """Read directive name (uppercase with underscores)."""
        result = []
        while self.peek() and (self.peek().isupper() or self.peek() == '_'):
            result.append(self.advance())
        return ''.join(result)
    
    def read_identifier(self) -> str:
        """Read identifier (alphanumeric + underscores)."""
        result = []
        while self.peek() and (self.peek().isalnum() or self.peek() == '_'):
            result.append(self.advance())
        return ''.join(result)
    
    def read_number(self) -> str:
        """Read number."""
        result = []
        while self.peek() and self.peek().isdigit():
            result.append(self.advance())
        return ''.join(result)
    
    def read_string(self, quote_char: str) -> str:
        """Read quoted string."""
        result = []
        self.advance()  # Skip opening quote
        
        while self.peek():
            char = self.peek()
            if char == quote_char:
                self.advance()  # Skip closing quote
                break
            elif char == '\\':
                self.advance()
                next_char = self.advance()
                if next_char:
                    # Handle escape sequences
                    escape_map = {'n': '\n', 't': '\t', 'r': '\r', '\\': '\\', quote_char: quote_char}
                    result.append(escape_map.get(next_char, next_char))
            else:
                result.append(self.advance())
        
        return ''.join(result)
    
    def read_path(self) -> str:
        """Read path (everything after directive until newline, excluding params)."""
        self.skip_whitespace()
        return self.read_until_newline().strip()
    
    def tokenize_directive_line(self, directive_name: str):
        """Tokenize a directive line with optional parameters and path."""
        line_start = self.line
        col_start = self.column
        
        # Map directive names to token types
        directive_map = {
            'CREATE': TokenType.CREATE,
            'DELETE': TokenType.DELETE,
            'MOVE': TokenType.MOVE,
            'READ': TokenType.READ,
            'TREE': TokenType.TREE,
            'SEARCH_AND_REPLACE': TokenType.SEARCH_AND_REPLACE,
            'OVERWRITE_FILE': TokenType.OVERWRITE_FILE,
            'FIND': TokenType.FIND,
            'BEFORE': TokenType.BEFORE,
            'END_BEFORE': TokenType.END_BEFORE,
            'AFTER': TokenType.AFTER,
            'END_AFTER': TokenType.END_AFTER,
            'END_CREATE': TokenType.END_CREATE,
            'END_OVERWRITE_FILE': TokenType.END_OVERWRITE_FILE,
            'END_SEARCH_AND_REPLACE': TokenType.END_SEARCH_AND_REPLACE,
        }
        
        token_type = directive_map.get(directive_name)
        if not token_type:
            self.error(f"Unknown directive: {directive_name}")
        
        self.tokens.append(Token(token_type, directive_name, line_start, col_start))
        
        self.skip_whitespace()
        
        # Check for parameters in parentheses
        if self.peek() == '(':
            self.tokenize_parameters()
        
        # Check if there's a path or other arguments after the directive
        self.skip_whitespace()
        remaining = self.read_until_newline().strip()
        
        if remaining:
            # For directives that take paths or other arguments
            self.tokens.append(Token(TokenType.PATH, remaining, self.line, self.column))
    
    def tokenize_parameters(self):
        """Tokenize parameters in parentheses: (key=value, key2=value2)."""
        self.advance()  # Skip '('
        self.tokens.append(Token(TokenType.LPAREN, '(', self.line, self.column - 1))
        
        self.skip_whitespace()
        
        while self.peek() and self.peek() != ')':
            # Read parameter name
            if self.peek().isalpha() or self.peek() == '_':
                param_name = self.read_identifier()
                self.tokens.append(Token(TokenType.IDENTIFIER, param_name, self.line, self.column - len(param_name)))
                
                self.skip_whitespace()
                
                # Expect '='
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.EQUALS, '=', self.line, self.column - 1))
                    
                    self.skip_whitespace()
                    
                    # Read value
                    if self.peek() in '"\'':
                        quote = self.peek()
                        value = self.read_string(quote)
                        self.tokens.append(Token(TokenType.STRING, value, self.line, self.column - len(value)))
                    elif self.peek() and self.peek().isdigit():
                        value = self.read_number()
                        self.tokens.append(Token(TokenType.NUMBER, value, self.line, self.column - len(value)))
                    elif self.peek() and self.peek().isalpha():
                        value = self.read_identifier()
                        self.tokens.append(Token(TokenType.IDENTIFIER, value, self.line, self.column - len(value)))
                    else:
                        self.error(f"Expected parameter value")
                
                self.skip_whitespace()
                
                # Check for comma
                if self.peek() == ',':
                    self.advance()
                    self.tokens.append(Token(TokenType.COMMA, ',', self.line, self.column - 1))
                    self.skip_whitespace()
            else:
                break
        
        # Expect ')'
        if self.peek() == ')':
            self.advance()
            self.tokens.append(Token(TokenType.RPAREN, ')', self.line, self.column - 1))
        else:
            self.error("Expected closing parenthesis")
    
    def skip_comment(self):
        """Skip a comment line (from # to end of line)."""
        if self.peek() == '#':
            # Skip everything until newline
            while self.peek() and self.peek() != '\n':
                self.advance()
    
    def tokenize(self) -> List[Token]:
        """Tokenize the entire input."""
        in_content_block = False
        content_buffer = []
        content_start_line = 0
        content_start_col = 0
        
        while self.pos < len(self.text):
            # Check for comments outside of content blocks
            if not in_content_block and self.peek() == '#':
                self.skip_comment()
                continue
            
            # Check if we're at a directive marker
            if self.peek() == '@' and self.peek(1) == 'K' and self.peek(2) == 'i' and self.peek(3) == 'f':
                # If inside a content block, only recognize END markers
                if in_content_block:
                    # Peek ahead to check if this is an END marker
                    saved_pos = self.pos
                    saved_line = self.line
                    saved_col = self.column
                    
                    # Temporarily advance to check directive name
                    for _ in range(4):  # Skip "@Kif"
                        self.advance()
                    self.skip_whitespace()
                    peek_directive = self.read_directive_name()
                    
                    # Restore position
                    self.pos = saved_pos
                    self.line = saved_line
                    self.column = saved_col
                    
                    # Only process if it's an END marker, otherwise treat as content
                    if peek_directive not in ['END_BEFORE', 'END_AFTER', 'END_CREATE', 
                                             'END_OVERWRITE_FILE', 'END_SEARCH_AND_REPLACE',
                                             'BEFORE', 'AFTER']:
                        # Not an END marker or block starter - treat as content
                        char = self.advance()
                        if char:
                            content_buffer.append(char)
                        continue
                    
                    # It's an END marker or block starter - save content and process directive
                    if content_buffer:
                        content = ''.join(content_buffer)
                        self.tokens.append(Token(TokenType.CONTENT, content, content_start_line, content_start_col))
                        content_buffer = []
                        in_content_block = False
                
                # Save position for directive start token
                line_start = self.line
                col_start = self.column
                
                # Skip "@Kif"
                for _ in range(4):
                    self.advance()
                
                # Add directive start token
                self.tokens.append(Token(TokenType.DIRECTIVE_START, '@Kif', line_start, col_start))
                
                # Skip whitespace
                self.skip_whitespace()
                
                # Read directive name
                directive_name = self.read_directive_name()
                
                if not directive_name:
                    self.error("Expected directive name after @Kif")
                
                # Tokenize the directive line
                self.tokenize_directive_line(directive_name)
                
                # Check if this directive starts a content block
                if directive_name in ['CREATE', 'OVERWRITE_FILE', 'SEARCH_AND_REPLACE']:
                    in_content_block = True
                    content_start_line = self.line
                    content_start_col = self.column
                
                # Check if this is an end marker that stops content collection
                if directive_name in ['END_BEFORE', 'END_AFTER', 'END_CREATE', 
                                     'END_OVERWRITE_FILE', 'END_SEARCH_AND_REPLACE']:
                    in_content_block = False
                
                # Check if this is BEFORE or AFTER which starts content collection
                if directive_name in ['BEFORE', 'AFTER']:
                    in_content_block = True
                    content_start_line = self.line
                    content_start_col = self.column
                
                # Add newline token if we're at a newline
                if self.peek() == '\n':
                    self.tokens.append(Token(TokenType.NEWLINE, '\\n', self.line, self.column))
                    self.advance()
            else:
                # We're in content - collect it
                if in_content_block:
                    char = self.advance()
                    if char:
                        content_buffer.append(char)
                else:
                    # Skip whitespace and newlines outside of directives
                    if self.peek() in ' \t\r\n':
                        self.advance()
                    else:
                        # Unexpected character outside directive
                        char = self.advance()
        
        # Save any remaining content
        if content_buffer:
            content = ''.join(content_buffer)
            self.tokens.append(Token(TokenType.CONTENT, content, content_start_line, content_start_col))
        
        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        
        return self.tokens
