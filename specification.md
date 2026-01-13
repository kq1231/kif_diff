# KifDiff Language Specification v2.0

## Overview
A `.kifdiff` file is a plain text file that contains one or more operations for modifying files. Each operation is defined by a set of directives with optional parameters.

## Core Directives

### `@Kif FILE <file_path>`
Specifies the target file for all subsequent operations until the next `@Kif FILE` directive.

**Example:**
```
@Kif FILE lib/widgets/ui_input.dart
```

---

## Operations

### 1. Create File

Creates a new file with the specified content. If the file already exists, it will be overwritten.

**Syntax:**
```
@Kif FILE <path/to/new_file.txt>
@Kif CREATE
... (file content goes here) ...
@Kif END_CREATE
```

**Example:**
```
@Kif FILE lib/constants.dart
@Kif CREATE
class AppConstants {
  static const String appName = 'My Awesome App';
  static const double defaultPadding = 16.0;
}
@Kif END_CREATE
```

---

### 2. Delete File

Deletes the specified file from the filesystem. **Note:** Files are automatically backed up before deletion (unless `--no-backup` is used when running the python file).

**Syntax:**
```
@Kif FILE <path/to/file_to_delete.txt>
@Kif DELETE
```

**Example:**
```
@Kif FILE lib/old_utils.dart
@Kif DELETE
```

---

### 3. Search and Replace

Finds a block of text in a file and replaces it with another block of text. This is the most powerful tool for modifying existing code.

**Syntax:**
```
@Kif FILE <path/to/target_file.dart>
@Kif SEARCH_AND_REPLACE
@Kif BEFORE
... (exact text to find) ...
@Kif END_BEFORE
@Kif AFTER
... (new text to replace it with) ...
@Kif END_AFTER
@Kif END_SEARCH_AND_REPLACE
```

**Important Notes:**
- The BEFORE block must match exactly (including whitespace)
- By default, only the first occurrence is replaced
- Files are automatically backed up before modification

**Example:**
```
@Kif FILE example/lib/app_bar_demo_page.dart
@Kif SEARCH_AND_REPLACE
@Kif BEFORE
            const SizedBox(height: 24),
            // Section: With Title Tap
@Kif END_BEFORE
@Kif AFTER
            const SizedBox(height: 24),
            // Section: Menu Button With Actions
            CodeViewer(
              title: 'Menu Button With Actions',
              code: '''UIAppBar(...)''',
              child: Column(...),
            ),
            const SizedBox(height: 24),
            // Section: With Title Tap
@Kif END_AFTER
@Kif END_SEARCH_AND_REPLACE
```

---

### 4. Read File

Reads the contents of a file and copies them to the clipboard along with the file path. This is useful for LLMs that need to examine multiple files.

**Syntax:**
```
@Kif READ <path/to/file_to_read.txt>
```

**Example:**
```
@Kif READ lib/example.dart
```

**Note:** This requires the `pyperclip` module to be installed. If not available, the content will be printed to the console instead.

---

### 5. Directory Tree

Displays a visual tree structure of a directory's contents.

**Syntax:**
```
@Kif TREE <path/to/directory>
```

**Example:**
```
@Kif TREE lib/
```

**Example with Parameters:**
```
@Kif TREE lib/(depth=2, show_hidden=true)
```

---

## Directive Parameters

Directives can accept parameters to modify their behavior. Parameters are specified in parentheses after the directive name.

**Syntax:**
```
@Kif DIRECTIVE_NAME(param1=value1, param2=value2)
```

### Available Parameters

#### SEARCH_AND_REPLACE Parameters

**`replace_all`** (boolean, default: `false`)
- When `true`, replaces all occurrences of the BEFORE block
- When `false`, replaces only the first occurrence
- **Important**: Even when using regex, `replace_all=true` is required to replace all matches. Without it, only the first regex match will be replaced.

**`count`** (integer, default: `1`)
- Specifies the exact number of occurrences to replace
- Only takes effect when `replace_all` is `false`
- Cannot be used together with `replace_all=true` (replace_all takes priority)
- Useful when you want to replace a specific number of occurrences but not all

**`ignore_whitespace`** (boolean, default: `false`)
- When `true`, ignores trailing whitespace on each line when matching
- Useful when editors auto-trim whitespace

**`fuzzy_match`** (boolean, default: `false`)
- When `true`, uses fuzzy matching to find similar content
- Reserved for future implementation

**`regex`** (boolean, default: `false`)
- When `true`, treats the BEFORE block as a regular expression pattern
- When `false`, treats the BEFORE block as literal text
- Useful for pattern matching and replacement

#### TREE Parameters

**`depth`** (integer, default: unlimited)
- Maximum directory depth to display
- Useful for limiting output in large directory structures

**`show_hidden`** (boolean, default: `false`)
- When `true`, includes hidden files and directories (those starting with `.`)
- When `false`, hides files and directories starting with `.`

**`include_files`** (boolean, default: `true`)
- When `true`, includes files in the tree output
- When `false`, shows only directories

**Example with Parameters:**
```
@Kif SEARCH_AND_REPLACE(replace_all=true, ignore_whitespace=true, regex=true)
@Kif BEFORE
old code
@Kif END_BEFORE
@Kif AFTER
new code
@Kif END_AFTER
@Kif END_SEARCH_AND_REPLACE
```

**Example with Count Parameter:**
```
@Kif SEARCH_AND_REPLACE(count=3)
@Kif BEFORE
old code
@Kif END_BEFORE
@Kif AFTER
new code
@Kif END_AFTER
@Kif END_SEARCH_AND_REPLACE
```

**Example with TREE Parameters:**
```
@Kif TREE lib/(depth=3, show_hidden=false, include_files=true)
```

Instructions for LLM: 

1. For repetition, you can set replace_all to true when using SEARCH_AND_REPLACE to replace all occurrences of the BEFORE block.

2. Use the count parameter to replace a specific number of occurrences.

3. ONLY WRITE WHAT IS NEEDED. THE KIFDIFF IS FOR THIS VERY REASON SO THAT YOU DONT HAVE TO WRITE FULL FILES. Make good use of regex where needed.

4. Use absolute paths and NOT relative paths.

5. READ and TREE directives do not require a preceding FILE directive.