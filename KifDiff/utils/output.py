"""Output utilities for KifDiff with beautiful rich formatting."""

try:
    from rich.console import Console
    from rich.theme import Theme
    from rich.table import Table
    from rich.panel import Panel
    from rich.tree import Tree as RichTree
    from rich import box
    
    # Custom theme for KifDiff
    custom_theme = Theme({
        "info": "cyan bold",
        "success": "green bold",
        "warning": "yellow bold",
        "error": "red bold",
        "tree": "blue",
    })
    
    console = Console(theme=custom_theme)
    RICH_SUPPORT = True
except ImportError:
    console = None
    RICH_SUPPORT = False


def print_success(msg):
    """Print success message in green."""
    if RICH_SUPPORT:
        console.print(msg, style="success")
    else:
        print(msg)


def print_error(msg):
    """Print error message in red."""
    if RICH_SUPPORT:
        console.print(msg, style="error")
    else:
        print(msg)


def print_warning(msg):
    """Print warning message in yellow."""
    if RICH_SUPPORT:
        console.print(msg, style="warning")
    else:
        print(msg)


def print_info(msg):
    """Print info message in cyan."""
    if RICH_SUPPORT:
        console.print(msg, style="info")
    else:
        print(msg)


def print_tree(msg):
    """Print tree output in blue."""
    if RICH_SUPPORT:
        console.print(msg, style="tree")
    else:
        print(msg)


def print_header(file_path, backup_dir=None):
    """Print beautiful header for KifDiff processing."""
    if RICH_SUPPORT:
        backup_text = backup_dir if backup_dir else "Disabled"
        console.print()
        console.print(Panel(
            f"[cyan bold]Processing:[/cyan bold] {file_path}\n"
            f"[dim]Backup:[/dim] {backup_text}",
            title="[bold magenta]⚡ KifDiff[/bold magenta]",
            border_style="magenta",
            padding=(0, 2)
        ))
        console.print()
    else:
        print(f"\n--- Processing KifDiff file: {file_path} ---")
        if backup_dir:
            print(f"Backup session: {backup_dir}")


def print_summary_table(stats):
    """Print beautiful summary table with statistics."""
    total_successful = stats.created + stats.deleted + stats.modified
    
    if RICH_SUPPORT:
        # Create summary table
        table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
        table.add_column("Operation", style="dim")
        table.add_column("Count", justify="right", style="bold")
        
        # Add rows with appropriate styling
        if stats.created > 0:
            table.add_row("✓ Files Created", f"[green]{stats.created}[/green]")
        else:
            table.add_row("Files Created", str(stats.created))
        
        if stats.modified > 0:
            table.add_row("✓ Files Modified", f"[blue]{stats.modified}[/blue]")
        else:
            table.add_row("Files Modified", str(stats.modified))
        
        if stats.deleted > 0:
            table.add_row("✓ Files Deleted", f"[magenta]{stats.deleted}[/magenta]")
        else:
            table.add_row("Files Deleted", str(stats.deleted))
        
        if stats.skipped > 0:
            table.add_row("⊘ Files Skipped", f"[yellow]{stats.skipped}[/yellow]")
        
        if stats.failed > 0:
            table.add_row("✗ Operations Failed", f"[red bold]{stats.failed}[/red bold]")
        
        # Create status message
        if stats.failed > 0:
            status_style = "red bold"
            if total_successful > 0:
                status_msg = f"✗ {stats.failed} failed, ✓ {total_successful} succeeded"
            else:
                status_msg = f"✗ {stats.failed} operations failed"
        elif total_successful > 0:
            status_style = "green bold"
            status_msg = f"✓ {total_successful} operations completed successfully!"
        else:
            status_style = "cyan"
            status_msg = "ℹ No file operations performed"
        
        # Print summary in a panel
        console.print()
        console.print(Panel(
            table,
            title="[bold cyan]📊 KifDiff Summary[/bold cyan]",
            subtitle=f"[{status_style}]{status_msg}[/{status_style}]",
            border_style="cyan",
            padding=(1, 2)
        ))
        console.print()
    else:
        # Fallback to simple output
        print("\n" + "="*50)
        print_info("SUMMARY")
        print("="*50)
        
        if total_successful > 0:
            print_success(f"✓ {total_successful} operations succeeded")
        
        print(f"  Files created:  {stats.created}")
        print(f"  Files deleted:  {stats.deleted}")
        print(f"  Files modified: {stats.modified}")
        
        if stats.skipped > 0:
            print_warning(f"  Files skipped:  {stats.skipped}")
        
        if stats.failed > 0:
            print_error(f"✗ {stats.failed} operations failed")
        elif total_successful == 0:
            print_info("No file operations performed")
        
        print("="*50)


def print_clipboard_summary(stats):
    """Print beautiful clipboard summary."""
    if RICH_SUPPORT:
        clipboard_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
        clipboard_table.add_column("Icon", style="cyan")
        clipboard_table.add_column("Item", style="dim")
        clipboard_table.add_column("Count", justify="right", style="bold green")
        
        if stats.clipboard_files:
            clipboard_table.add_row("📄", "Files read", str(len(stats.clipboard_files)))
        if stats.clipboard_dirs:
            clipboard_table.add_row("📁", "Directory trees", str(len(stats.clipboard_dirs)))
        if stats.clipboard_errors:
            clipboard_table.add_row("❌", "Errors", f"[red]{len(stats.clipboard_errors)}[/red]")
        
        console.print()
        console.print("[green bold]✓ Copied to clipboard:[/green bold]")
        console.print(clipboard_table)
    else:
        total_items = len(stats.clipboard_files) + len(stats.clipboard_dirs) + len(stats.clipboard_errors)
        print_success(f"\nClipboard: Copied {total_items} item(s) to clipboard:")
        if stats.clipboard_files:
            print(f"  - {len(stats.clipboard_files)} file(s) read")
        if stats.clipboard_dirs:
            print(f"  - {len(stats.clipboard_dirs)} directory tree(s)")
        if stats.clipboard_errors:
            print_warning(f"  - {len(stats.clipboard_errors)} error(s)")


def print_ast_tree(program):
    """Print beautiful AST tree visualization - SubhanAllah!"""
    if not RICH_SUPPORT:
        print("\n--- AST Structure ---")
        print(f"Program with {len(program.directives)} directive(s)")
        for i, directive in enumerate(program.directives, 1):
            print(f"  {i}. {type(directive).__name__}")
        print("--- End AST ---\n")
        return
    
    # Create root tree
    tree = RichTree(
        "[bold magenta]🌳 Abstract Syntax Tree (AST)[/bold magenta]",
        guide_style="cyan"
    )
    
    # Add program node
    program_node = tree.add(f"[bold cyan]Program[/bold cyan] [dim]({len(program.directives)} directives)[/dim]")
    
    # Add each directive
    for i, directive in enumerate(program.directives, 1):
        directive_type = type(directive).__name__.replace("Directive", "")
        
        # Color coding by directive type
        if directive_type in ["Create", "CreateDirective"]:
            icon = "📝"
            color = "green"
        elif directive_type in ["Delete", "DeleteDirective"]:
            icon = "🗑️"
            color = "red"
        elif directive_type in ["Move", "MoveDirective"]:
            icon = "🔄"
            color = "yellow"
        elif directive_type in ["Read", "ReadDirective"]:
            icon = "📖"
            color = "blue"
        elif directive_type in ["Tree", "TreeDirective"]:
            icon = "🌲"
            color = "blue"
        elif directive_type in ["OverwriteFile", "OverwriteFileDirective"]:
            icon = "✏️"
            color = "magenta"
        elif directive_type in ["SearchAndReplace", "SearchAndReplaceDirective"]:
            icon = "🔍"
            color = "cyan"
        elif directive_type in ["Find", "FindDirective"]:
            icon = "🔎"
            color = "blue"
        else:
            icon = "📄"
            color = "white"
        
        # Create directive node
        directive_node = program_node.add(
            f"[{color} bold]{icon} {directive_type}[/{color} bold] [dim](line {directive.line})[/dim]"
        )
        
        # Add directive details
        if hasattr(directive, 'path'):
            path_parts = directive.path.split('/')
            filename = path_parts[-1] if path_parts else directive.path
            directive_node.add(f"[yellow]📁 Path:[/yellow] [dim]{filename}[/dim]")
        
        if hasattr(directive, 'source') and hasattr(directive, 'dest'):
            directive_node.add(f"[yellow]📤 Source:[/yellow] [dim]{directive.source.split('/')[-1]}[/dim]")
            directive_node.add(f"[yellow]📥 Dest:[/yellow] [dim]{directive.dest.split('/')[-1]}[/dim]")
        
        if hasattr(directive, 'params') and directive.params:
            params_node = directive_node.add("[yellow]⚙️  Parameters:[/yellow]")
            for key, value in directive.params.items():
                params_node.add(f"[dim]{key}=[/dim][green]{value}[/green]")
        
        if hasattr(directive, 'blocks') and directive.blocks:
            blocks_node = directive_node.add(f"[yellow]🔄 Blocks:[/yellow] [dim]({len(directive.blocks)} replacements)[/dim]")
            for j, block in enumerate(directive.blocks, 1):
                block_node = blocks_node.add(f"[cyan]Block {j}[/cyan]")
                before_preview = block.before[:40] + "..." if len(block.before) > 40 else block.before
                after_preview = block.after[:40] + "..." if len(block.after) > 40 else block.after
                block_node.add(f"[red]Before:[/red] [dim]{before_preview}[/dim]")
                block_node.add(f"[green]After:[/green] [dim]{after_preview}[/dim]")
        
        if hasattr(directive, 'content') and directive.content:
            content_preview = directive.content[:50] + "..." if len(directive.content) > 50 else directive.content
            directive_node.add(f"[yellow]📝 Content:[/yellow] [dim]{content_preview}[/dim]")
    
    # Print the tree
    console.print()
    console.print(Panel(
        tree,
        title="[bold cyan]🎯 Parsed Structure[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    ))
    console.print()
