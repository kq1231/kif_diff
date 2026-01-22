"""KifDiff file parsing and execution."""

import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from .stats import Stats
from .lexer import Lexer, Token, TokenType
from .ast_nodes import (
    Program, Directive, CreateDirective, DeleteDirective, MoveDirective,
    ReadDirective, TreeDirective, OverwriteFileDirective, 
    SearchAndReplaceDirective, FindDirective, RunDirective, BeforeAfterBlock
)
from .executor import ASTExecutor
from utils.output import RICH_SUPPORT, print_info, print_error, print_header, print_clipboard_summary, print_ast_tree


class Parser:
    """Parses tokens into an Abstract Syntax Tree."""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
    
    def error(self, msg: str, token: Optional[Token] = None):
        """Raise a parser error."""
        if token is None:
            token = self.current_token()
        raise SyntaxError(f"Parser error at line {token.line}, column {token.column}: {msg}")
    
    def current_token(self) -> Token:
        """Get current token."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]  # Return EOF
    
    def peek(self, offset: int = 0) -> Token:
        """Peek at token at current position + offset."""
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return self.tokens[-1]  # Return EOF
    
    def advance(self) -> Token:
        """Advance to next token and return current."""
        token = self.current_token()
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return token
    
    def expect(self, token_type: TokenType) -> Token:
        """Expect a specific token type and advance."""
        token = self.current_token()
        if token.type != token_type:
            self.error(f"Expected {token_type.name}, got {token.type.name}", token)
        return self.advance()
    
    def skip_newlines(self):
        """Skip any newline tokens."""
        while self.current_token().type == TokenType.NEWLINE:
            self.advance()
    
    def parse_parameters(self) -> Dict[str, Any]:
        """Parse parameter list: (key=value, key2=value2)."""
        params = {}
        
        self.expect(TokenType.LPAREN)
        
        while self.current_token().type != TokenType.RPAREN:
            # Parse key
            key_token = self.expect(TokenType.IDENTIFIER)
            key = key_token.value
            
            # Parse =
            self.expect(TokenType.EQUALS)
            
            # Parse value
            value_token = self.current_token()
            if value_token.type == TokenType.STRING:
                value = self.advance().value
            elif value_token.type == TokenType.NUMBER:
                value = int(self.advance().value)
            elif value_token.type == TokenType.IDENTIFIER:
                # Handle true/false/other identifiers
                val_str = self.advance().value.lower()
                if val_str == 'true':
                    value = True
                elif val_str == 'false':
                    value = False
                else:
                    value = val_str
            else:
                self.error(f"Expected parameter value, got {value_token.type.name}", value_token)
            
            params[key] = value
            
            # Check for comma
            if self.current_token().type == TokenType.COMMA:
                self.advance()
        
        self.expect(TokenType.RPAREN)
        
        return params
    
    def parse_path(self) -> str:
        """Parse a path argument."""
        token = self.current_token()
        if token.type == TokenType.PATH:
            return self.advance().value
        self.error(f"Expected path, got {token.type.name}", token)
    
    def parse_content_until(self, end_token_type: TokenType) -> str:
        """Parse content until we hit a specific end marker."""
        content_parts = []
        
        self.skip_newlines()
        
        while self.current_token().type != end_token_type and self.current_token().type != TokenType.EOF:
            token = self.current_token()
            
            if token.type == TokenType.CONTENT:
                content_parts.append(self.advance().value)
            elif token.type == TokenType.NEWLINE:
                self.advance()
            elif token.type == TokenType.DIRECTIVE_START:
                # Check if next token is the end marker
                next_tok = self.peek(1)
                if next_tok.type == end_token_type:
                    break
                else:
                    self.error(f"Unexpected directive in content block", token)
            else:
                self.error(f"Unexpected token in content: {token.type.name}", token)
        
        return ''.join(content_parts)
    
    def parse_before_after_block(self) -> BeforeAfterBlock:
        """Parse a BEFORE/AFTER block pair."""
        # Expect @Kif BEFORE
        self.expect(TokenType.DIRECTIVE_START)
        self.expect(TokenType.BEFORE)
        self.skip_newlines()
        
        # Parse BEFORE content
        before_content = self.parse_content_until(TokenType.END_BEFORE)
        
        # Expect @Kif END_BEFORE
        self.expect(TokenType.DIRECTIVE_START)
        self.expect(TokenType.END_BEFORE)
        self.skip_newlines()
        
        # Expect @Kif AFTER
        self.expect(TokenType.DIRECTIVE_START)
        self.expect(TokenType.AFTER)
        self.skip_newlines()
        
        # Parse AFTER content
        after_content = self.parse_content_until(TokenType.END_AFTER)
        
        # Expect @Kif END_AFTER
        self.expect(TokenType.DIRECTIVE_START)
        self.expect(TokenType.END_AFTER)
        self.skip_newlines()
        
        # Remove trailing newline if present for cleaner matching
        if before_content.endswith('\n'):
            before_content = before_content[:-1]
        if after_content.endswith('\n'):
            after_content = after_content[:-1]
        
        return BeforeAfterBlock(before=before_content, after=after_content)
    
    def parse_create_directive(self, line: int, column: int) -> CreateDirective:
        """Parse CREATE directive."""
        params = {}
        
        # Check for parameters
        if self.current_token().type == TokenType.LPAREN:
            params = self.parse_parameters()
        
        # Parse path
        path = self.parse_path()
        self.skip_newlines()
        
        # Parse content until END_CREATE
        content = self.parse_content_until(TokenType.END_CREATE)
        
        # Expect @Kif END_CREATE
        self.expect(TokenType.DIRECTIVE_START)
        self.expect(TokenType.END_CREATE)
        self.skip_newlines()
        
        return CreateDirective(line=line, column=column, params=params, path=path, content=content)
    
    def parse_delete_directive(self, line: int, column: int) -> DeleteDirective:
        """Parse DELETE directive."""
        params = {}
        
        # Check for parameters
        if self.current_token().type == TokenType.LPAREN:
            params = self.parse_parameters()
        
        # Parse path
        path = self.parse_path()
        self.skip_newlines()
        
        return DeleteDirective(line=line, column=column, params=params, path=path)
    
    def parse_move_directive(self, line: int, column: int) -> MoveDirective:
        """Parse MOVE directive."""
        params = {}
        
        # Check for parameters
        if self.current_token().type == TokenType.LPAREN:
            params = self.parse_parameters()
        
        # Parse paths (source and dest separated by space)
        path_token = self.current_token()
        if path_token.type != TokenType.PATH:
            self.error("Expected source and destination paths for MOVE", path_token)
        
        paths = self.advance().value
        parts = paths.split(None, 1)  # Split on first whitespace
        
        if len(parts) < 2:
            self.error("MOVE requires both source and destination paths", path_token)
        
        source = parts[0]
        dest = parts[1]
        
        self.skip_newlines()
        
        return MoveDirective(line=line, column=column, params=params, source=source, dest=dest)
    
    def parse_read_directive(self, line: int, column: int) -> ReadDirective:
        """Parse READ directive."""
        params = {}
        
        # Check for parameters
        if self.current_token().type == TokenType.LPAREN:
            params = self.parse_parameters()
        
        # Parse path
        path = self.parse_path()
        self.skip_newlines()
        
        return ReadDirective(line=line, column=column, params=params, path=path)
    
    def parse_tree_directive(self, line: int, column: int) -> TreeDirective:
        """Parse TREE directive."""
        params = {}
        
        # Check for parameters
        if self.current_token().type == TokenType.LPAREN:
            params = self.parse_parameters()
        
        # Parse path
        path = self.parse_path()
        self.skip_newlines()
        
        return TreeDirective(line=line, column=column, params=params, path=path)
    
    def parse_overwrite_file_directive(self, line: int, column: int) -> OverwriteFileDirective:
        """Parse OVERWRITE_FILE directive."""
        params = {}
        
        # Check for parameters
        if self.current_token().type == TokenType.LPAREN:
            params = self.parse_parameters()
        
        # Parse path
        path = self.parse_path()
        self.skip_newlines()
        
        # Parse content until END_OVERWRITE_FILE
        content = self.parse_content_until(TokenType.END_OVERWRITE_FILE)
        
        # Expect @Kif END_OVERWRITE_FILE
        self.expect(TokenType.DIRECTIVE_START)
        self.expect(TokenType.END_OVERWRITE_FILE)
        self.skip_newlines()
        
        return OverwriteFileDirective(line=line, column=column, params=params, path=path, content=content)
    
    def parse_search_and_replace_directive(self, line: int, column: int) -> SearchAndReplaceDirective:
        """Parse SEARCH_AND_REPLACE directive with multiple BEFORE/AFTER blocks."""
        params = {}
        
        # Check for parameters
        if self.current_token().type == TokenType.LPAREN:
            params = self.parse_parameters()
        
        # Parse path
        path = self.parse_path()
        self.skip_newlines()
        
        # Parse multiple BEFORE/AFTER blocks
        blocks = []
        
        while True:
            token = self.current_token()
            
            # Check if we're at the end of SEARCH_AND_REPLACE
            if token.type == TokenType.DIRECTIVE_START:
                next_tok = self.peek(1)
                if next_tok.type == TokenType.END_SEARCH_AND_REPLACE:
                    break
                elif next_tok.type == TokenType.BEFORE:
                    # Parse another BEFORE/AFTER block
                    block = self.parse_before_after_block()
                    blocks.append(block)
                else:
                    self.error(f"Expected BEFORE or END_SEARCH_AND_REPLACE, got {next_tok.type.name}", next_tok)
            elif token.type == TokenType.EOF:
                self.error("Unexpected EOF in SEARCH_AND_REPLACE block", token)
            else:
                self.advance()
        
        # Expect @Kif END_SEARCH_AND_REPLACE
        self.expect(TokenType.DIRECTIVE_START)
        self.expect(TokenType.END_SEARCH_AND_REPLACE)
        self.skip_newlines()
        
        return SearchAndReplaceDirective(line=line, column=column, params=params, path=path, blocks=blocks)
    
    def parse_find_directive(self, line: int, column: int) -> FindDirective:
        """Parse FIND directive."""
        params = {}
        
        # Check for parameters
        if self.current_token().type == TokenType.LPAREN:
            params = self.parse_parameters()
        
        # Parse path
        path = self.parse_path()
        self.skip_newlines()
        
        return FindDirective(line=line, column=column, params=params, path=path)
    
    def parse_run_directive(self, line: int, column: int) -> RunDirective:
        """Parse RUN directive."""
        params = {}
        
        # Check for parameters
        if self.current_token().type == TokenType.LPAREN:
            params = self.parse_parameters()
        
        # Parse command (everything after RUN until newline)
        command = self.parse_path()
        self.skip_newlines()
        
        return RunDirective(line=line, column=column, params=params, command=command)
    
    def parse_directive(self) -> Optional[Directive]:
        """Parse a single directive."""
        # Expect @Kif
        token = self.current_token()
        if token.type == TokenType.EOF:
            return None
        
        if token.type != TokenType.DIRECTIVE_START:
            self.error(f"Expected @Kif directive, got {token.type.name}", token)
        
        directive_start = self.advance()
        line = directive_start.line
        column = directive_start.column
        
        # Get directive type
        directive_token = self.current_token()
        self.advance()
        
        # Parse specific directive
        if directive_token.type == TokenType.CREATE:
            return self.parse_create_directive(line, column)
        elif directive_token.type == TokenType.DELETE:
            return self.parse_delete_directive(line, column)
        elif directive_token.type == TokenType.MOVE:
            return self.parse_move_directive(line, column)
        elif directive_token.type == TokenType.READ:
            return self.parse_read_directive(line, column)
        elif directive_token.type == TokenType.TREE:
            return self.parse_tree_directive(line, column)
        elif directive_token.type == TokenType.OVERWRITE_FILE:
            return self.parse_overwrite_file_directive(line, column)
        elif directive_token.type == TokenType.SEARCH_AND_REPLACE:
            return self.parse_search_and_replace_directive(line, column)
        elif directive_token.type == TokenType.FIND:
            return self.parse_find_directive(line, column)
        elif directive_token.type == TokenType.RUN:
            return self.parse_run_directive(line, column)
        else:
            self.error(f"Unknown directive: {directive_token.value}", directive_token)
    
    def parse(self) -> Program:
        """Parse tokens into an AST."""
        program = Program()
        
        self.skip_newlines()
        
        while self.current_token().type != TokenType.EOF:
            directive = self.parse_directive()
            if directive:
                program.directives.append(directive)
        
        return program


def parse_kifdiff(file_path, stats=None, args=None):
    """Parses and executes a .kifdiff file using the new lexer/parser/AST pipeline."""
    if stats is None:
        stats = Stats()
    
    # Initialize session backup directory for this run
    global session_backup_dir
    session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_backup_dir = os.path.join(args.backup_dir, f"session_{session_timestamp}")
    
    backup_dir = session_backup_dir if args and not args.no_backup else None
    print_header(file_path, backup_dir)
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print_error(f"FATAL ERROR: KifDiff file '{file_path}' not found.")
        stats.failed += 1
        return stats

    try:
        # Tokenize
        if args and args.verbose:
            print_info("Tokenizing...")
        lexer = Lexer(content)
        tokens = lexer.tokenize()
        
        if args and args.verbose:
            print_info(f"Generated {len(tokens)} tokens")
        
        # Parse to AST
        if args and args.verbose:
            print_info("Parsing to AST...")
        parser = Parser(tokens)
        program = parser.parse()
        
        if args and args.verbose:
            print_info(f"Parsed {len(program.directives)} directive(s)")
            if RICH_SUPPORT:
                # Show beautiful AST tree - SubhanAllah!
                print_ast_tree(program)
        
        # Execute AST
        if args and args.verbose:
            print_info("Executing directives...")
        executor = ASTExecutor(stats, args)
        executor.execute(program)
        
    except SyntaxError as e:
        print_error(f"SYNTAX ERROR: {e}")
        if args and args.verbose:
            import traceback
            traceback.print_exc()
        stats.failed += 1
        return stats
    except Exception as e:
        print_error(f"ERROR: {e}")
        if args and args.verbose:
            import traceback
            traceback.print_exc()
            stats.failed += 1
        return stats

    # Copy accumulated clipboard buffer to clipboard
    if stats.clipboard_buffer:
        try:
            import pyperclip
            combined_content = ''.join(stats.clipboard_buffer)
            pyperclip.copy(combined_content)
            print_clipboard_summary(stats)
        except ImportError:
            print_error("\nERROR: pyperclip module not installed. Install it with 'pip install pyperclip'")
            print("Content that would have been copied to clipboard:")
            print("="*60)
            print(''.join(stats.clipboard_buffer))
            print("="*60)

    stats.print_summary()
    return stats