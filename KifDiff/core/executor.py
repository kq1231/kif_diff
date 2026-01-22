"""AST Executor - Executes directives from the AST."""

from .ast_nodes import (
    Program, CreateDirective, DeleteDirective, MoveDirective,
    ReadDirective, TreeDirective, OverwriteFileDirective,
    SearchAndReplaceDirective, FindDirective, RunDirective
)
from .executors import (
    CreateExecutor as CreateExecutorImpl,
    DeleteExecutor as DeleteExecutorImpl,
    MoveExecutor as MoveExecutorImpl,
    ReadExecutor as ReadExecutorImpl,
    TreeExecutor as TreeExecutorImpl,
    SearchReplaceExecutor,
    FindExecutor as FindExecutorImpl
)
from .executors.overwrite import OverwriteExecutor as OverwriteExecutorImpl
from .stats import Stats
from utils.output import print_info, print_error


class ASTExecutor:
    """Executes directives from an AST."""
    
    def __init__(self, stats: Stats = None, args=None):
        self.stats = stats or Stats()
        self.args = args
        
        # Initialize directive implementations
        self.create_impl = CreateExecutorImpl()
        self.delete_impl = DeleteExecutorImpl()
        self.move_impl = MoveExecutorImpl()
        self.read_impl = ReadExecutorImpl()
        self.tree_impl = TreeExecutorImpl()
        self.overwrite_impl = OverwriteExecutorImpl()
        self.search_replace_impl = SearchReplaceExecutor()
        self.find_impl = FindExecutorImpl()

    
    def execute(self, program: Program):
        """Execute all directives in the program."""
        for directive in program.directives:
            try:
                self.execute_directive(directive)
            except Exception as e:
                print_error(f"Error executing directive at line {directive.line}: {e}")
                if self.args and self.args.verbose:
                    import traceback
                    traceback.print_exc()
                self.stats.failed += 1
    
    def execute_directive(self, directive):
        """Execute a single directive."""
        if isinstance(directive, CreateDirective):
            self.execute_create(directive)
        elif isinstance(directive, DeleteDirective):
            self.execute_delete(directive)
        elif isinstance(directive, MoveDirective):
            self.execute_move(directive)
        elif isinstance(directive, ReadDirective):
            self.execute_read(directive)
        elif isinstance(directive, TreeDirective):
            self.execute_tree(directive)
        elif isinstance(directive, OverwriteFileDirective):
            self.execute_overwrite(directive)
        elif isinstance(directive, SearchAndReplaceDirective):
            self.execute_search_replace(directive)
        elif isinstance(directive, FindDirective):
            self.execute_find(directive)
        elif isinstance(directive, RunDirective):
            self.execute_run(directive)
        else:
            print_error(f"Unknown directive type: {type(directive).__name__}")
            self.stats.failed += 1
    
    def execute_create(self, directive: CreateDirective):
        """Execute CREATE directive."""
        self.create_impl.execute(
            directive.path,
            directive.content,
            self.stats,
            directive.line,
            self.args
        )
    
    def execute_delete(self, directive: DeleteDirective):
        """Execute DELETE directive."""
        self.delete_impl.execute(
            directive.path,
            self.stats,
            directive.line,
            self.args
        )
    
    def execute_move(self, directive: MoveDirective):
        """Execute MOVE directive."""
        self.move_impl.execute(
            directive.source,
            directive.dest,
            self.stats,
            directive.line,
            self.args
        )
    
    def execute_read(self, directive: ReadDirective):
        """Execute READ directive."""
        self.read_impl.execute(
            directive.path,
            self.stats,
            directive.line,
            self.args
        )
    
    def execute_tree(self, directive: TreeDirective):
        """Execute TREE directive."""
        self.tree_impl.execute(
            directive.path,
            directive.params,
            self.stats,
            directive.line,
            self.args
        )
    
    def execute_overwrite(self, directive: OverwriteFileDirective):
        """Execute OVERWRITE_FILE directive."""
        self.overwrite_impl.execute(
            directive.path,
            directive.content,
            self.stats,
            directive.line,
            self.args
        )
    
    def execute_search_replace(self, directive: SearchAndReplaceDirective):
        """Execute SEARCH_AND_REPLACE directive."""
        self.search_replace_impl.execute(
            directive.path,
            directive.blocks,
            directive.params,
            self.stats,
            directive.line,
            self.args
        )
    
    def execute_find(self, directive: FindDirective):
        """Execute FIND directive."""
        self.find_impl.execute(
            directive.path,
            directive.params,
            self.stats,
            directive.line,
            self.args
        )
    
    def execute_run(self, directive: RunDirective):
        """Execute RUN directive."""
        from .executors.run import execute_run
        execute_run(directive, self.stats, self.args)
