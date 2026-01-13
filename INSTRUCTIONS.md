# KifDiff Instructions for LLMs v2.0

## 🚨 CRITICAL WORKFLOW: Two-Phase Process

KifDiff operates in **TWO DISTINCT PHASES** that must be executed separately:

### Phase 1: INQUIRY (Information Gathering)
**Purpose:** Gather information about the codebase before making changes  
**Action:** Create a `.kifdiff` file with ONLY `@Kif READ` and/or `@Kif TREE` directives  
**Stop Here:** Wait for the user to run this file and provide you with the results

### Phase 2: EXECUTION (Making Changes)
**Purpose:** Apply actual code modifications based on inquiry results  
**Action:** Create a `.kifdiff` file with `CREATE`, `DELETE`, or `SEARCH_AND_REPLACE` operations  
**Timing:** Only after receiving the inquiry results from the user

### ⚠️ NEVER COMBINE PHASES
**DO NOT** write both inquiry and execution in the same response or file. You cannot make informed changes without first seeing the inquiry results!

### 📝 ALWAYS USE CODE BLOCKS
**ALL KifDiff content must be wrapped in code blocks.** This makes it easy for users to copy and save as `.kifdiff` files.

**Bad Example:**
```
Here's the inquiry file:
@Kif READ lib/example.dart
@Kif TREE lib/

And here's the changes file:
@Kif FILE lib/example.dart
@Kif SEARCH_AND_REPLACE
...
```

**Good Example:**
```
I need to examine the codebase first. Please run this inquiry file:

```kifdiff
@Kif READ lib/example.dart
@Kif TREE lib/
```

Once you provide the results, I'll create the execution file with the necessary changes.
```

---

## Core Directives

### `@Kif FILE <absolute_path>`
Specifies the target file for subsequent operations.

**Important:**
- Use **absolute paths**, not relative paths
- Required for: `DELETE`, `SEARCH_AND_REPLACE`
- Not required for: `CREATE`, `READ`, `TREE`, `MOVE` (these directives specify their own file paths)

**Example:**
```
@Kif FILE /home/user/project/lib/widgets/ui_input.dart
```

---

## Phase 1: INQUIRY Operations

### `@Kif READ <absolute_path>`
Reads a file's contents and copies it to clipboard (or prints to console).

**Use when you need to:**
- Examine existing code before modifying it
- Understand the current implementation
- Check file structure or dependencies

**Example:**
```
@Kif READ /home/user/project/lib/example.dart
```

### `@Kif TREE <absolute_path>(parameters)`
Displays directory structure as a visual tree.

**Parameters:**
- `depth=N` - Maximum directory depth (default: unlimited)
- `show_hidden=true/false` - Include hidden files (default: false)
- `include_files=true/false` - Show files or only directories (default: true)

**Use when you need to:**
- Understand project structure
- Find related files
- Locate where to create new files

**Examples:**
```
@Kif TREE /home/user/project/lib/

@Kif TREE /home/user/project/(depth=2, show_hidden=false)

@Kif TREE /home/user/project/lib/widgets/(depth=1, include_files=false)
```

---

## Phase 2: EXECUTION Operations

### 1. Create File

Creates a new file (overwrites if exists).

**Syntax:**
```
@Kif CREATE <absolute_path>
... (file content) ...
@Kif END_CREATE
```

**Important:**
- Use **absolute paths** directly in the CREATE directive
- Does NOT require `@Kif FILE` directive
- Creates parent directories automatically if they don't exist
- Overwrites the file if it already exists (automatically backed up)

**Example:**
```
@Kif CREATE /home/user/project/lib/constants.dart
class AppConstants {
  static const String appName = 'My Awesome App';
  static const double defaultPadding = 16.0;
}
@Kif END_CREATE
```

---

### 2. Delete File

Deletes a file (automatically backed up).

**Syntax:**
```
@Kif FILE <absolute_path>
@Kif DELETE
```

**Example:**
```
@Kif FILE /home/user/project/lib/old_utils.dart
@Kif DELETE
```

---

### 3. Move/Rename File or Directory

Moves or renames files and directories (automatically backed up).

**Syntax:**
```
@Kif MOVE <source_path> <destination_path>
```

**Important:**
- Use **absolute paths** for both source and destination
- Does NOT require `@Kif FILE` directive
- Works for both files and directories
- Automatically creates destination directories if they don't exist
- Source file/directory is backed up before moving

**Use Cases:**
- Rename a file: `@Kif MOVE /path/old_name.dart /path/new_name.dart`
- Move to different directory: `@Kif MOVE /path/file.dart /new/path/file.dart`
- Rename and move: `@Kif MOVE /old/path/old_name.dart /new/path/new_name.dart`
- Move entire directory: `@Kif MOVE /old/dir /new/dir`

**Examples:**
```
# Rename a file
@Kif MOVE /home/user/project/lib/old_utils.dart /home/user/project/lib/new_utils.dart

# Move file to different directory
@Kif MOVE /home/user/project/lib/utils.dart /home/user/project/lib/helpers/utils.dart

# Move and rename
@Kif MOVE /home/user/project/lib/old_name.dart /home/user/project/lib/core/new_name.dart

# Move entire directory
@Kif MOVE /home/user/project/lib/old_widgets /home/user/project/lib/components
```

---

### 4. Search and Replace

Finds and replaces text blocks. **Most powerful operation.**

**Syntax:**
```
@Kif FILE <absolute_path>
@Kif SEARCH_AND_REPLACE(parameters)
@Kif BEFORE
... (exact text to find) ...
@Kif END_BEFORE
@Kif AFTER
... (replacement text) ...
@Kif END_AFTER
@Kif END_SEARCH_AND_REPLACE
```

**Parameters:**

- **`replace_all=true/false`** (default: false)
  - `true`: Replace all occurrences
  - `false`: Replace only first occurrence
  - **Important:** Even with regex, you need `replace_all=true` to replace all matches

- **`count=N`** (default: 1)
  - Replace exactly N occurrences
  - Only works when `replace_all=false`
  - Useful for replacing specific instances without replacing all

- **`regex=true/false`** (default: false)
  - `true`: Treat BEFORE block as regex pattern
  - `false`: Treat BEFORE block as literal text

- **`ignore_whitespace=true/false`** (default: false)
  - `true`: Ignore trailing whitespace when matching
  - Useful when editors auto-trim whitespace

**Critical Rules:**
- BEFORE block must match exactly (including whitespace)
- Use absolute paths
- Files are automatically backed up

**Example - Simple Replacement:**
```
@Kif FILE /home/user/project/lib/ui_button.dart
@Kif SEARCH_AND_REPLACE
@Kif BEFORE
  void onPressed() {
    print('Button pressed');
  }
@Kif END_BEFORE
@Kif AFTER
  void onPressed() {
    print('Button pressed');
    _handleButtonPress();
  }
@Kif END_AFTER
@Kif END_SEARCH_AND_REPLACE
```

**Example - Replace All Occurrences:**
```
@Kif FILE /home/user/project/lib/theme.dart
@Kif SEARCH_AND_REPLACE(replace_all=true)
@Kif BEFORE
Color.blue
@Kif END_BEFORE
@Kif AFTER
Color(0xFF2196F3)
@Kif END_AFTER
@Kif END_SEARCH_AND_REPLACE
```

**Example - Replace Specific Count:**
```
@Kif FILE /home/user/project/lib/logger.dart
@Kif SEARCH_AND_REPLACE(count=3)
@Kif BEFORE
print(
@Kif END_BEFORE
@Kif AFTER
debugPrint(
@Kif END_AFTER
@Kif END_SEARCH_AND_REPLACE
```

**Example - Using Regex:**
```
@Kif FILE /home/user/project/lib/config.dart
@Kif SEARCH_AND_REPLACE(regex=true, replace_all=true)
@Kif BEFORE
const int timeout = \d+;
@Kif END_BEFORE
@Kif AFTER
const int timeout = 5000;
@Kif END_AFTER
@Kif END_SEARCH_AND_REPLACE
```

---

## Best Practices for LLMs

### 1. Always Start with Inquiry
Before making any changes, understand the codebase structure.

### 2. Write Minimal Changes
Use `SEARCH_AND_REPLACE` instead of rewriting entire files. Only include the specific code blocks that need modification.

**Exception:** When the new content is drastically smaller than the original file, use `DELETE` + `CREATE` instead of multiple `SEARCH_AND_REPLACE` operations.

**Example scenario:** If a file currently has 1000 lines but the new version only needs 10 lines, it's more efficient to:
```kifdiff
@Kif FILE /path/to/large_file.dart
@Kif DELETE

@Kif CREATE /path/to/large_file.dart
... (new 10 lines of content) ...
@Kif END_CREATE
```

Rather than using multiple `SEARCH_AND_REPLACE` operations to remove most of the content. Use your judgment: if you're removing more than 80% of a file's content, DELETE + CREATE is usually better.

### 3. Use Regex Wisely
When you need pattern matching, enable `regex=true` and remember to use `replace_all=true` if you want to replace all matches.

### 4. Be Precise with BEFORE Blocks
The BEFORE block must match exactly. If unsure about whitespace, use `ignore_whitespace=true`.

### 5. Use Absolute Paths
Never use relative paths. Always specify the full path from the project root.

### 6. Multiple Files and Operations
You can operate on multiple files and use different operations in a single `.kifdiff`:
```
@Kif FILE /path/to/first.dart
@Kif SEARCH_AND_REPLACE
...
@Kif END_SEARCH_AND_REPLACE

@Kif FILE /path/to/second.dart
@Kif SEARCH_AND_REPLACE
...
@Kif END_SEARCH_AND_REPLACE

@Kif MOVE /path/to/old_file.dart /path/to/new_location/new_file.dart

@Kif FILE /path/to/third.dart
@Kif DELETE
```

---

## Common Workflow Example

**User Request:** "Add a new button to the home screen and update the theme colors"

**Your Response - Phase 1:**
```
I'll help you add a button and update the theme. First, let me examine the relevant files:

```kifdiff
@Kif READ /home/user/project/lib/screens/home_screen.dart
@Kif READ /home/user/project/lib/theme/app_theme.dart
@Kif TREE /home/user/project/lib/widgets/
```

Please run this inquiry file and share the results.
```

**After User Provides Results - Phase 2:**
```
Based on the files you shared, here's the execution file:

```kifdiff
@Kif FILE /home/user/project/lib/screens/home_screen.dart
@Kif SEARCH_AND_REPLACE
@Kif BEFORE
      body: Center(
        child: Text('Welcome'),
      ),
@Kif END_BEFORE
@Kif AFTER
      body: Center(
        child: Column(
          children: [
            Text('Welcome'),
            ElevatedButton(
              onPressed: () {},
              child: Text('Click Me'),
            ),
          ],
        ),
      ),
@Kif END_AFTER
@Kif END_SEARCH_AND_REPLACE

@Kif FILE /home/user/project/lib/theme/app_theme.dart
@Kif SEARCH_AND_REPLACE(replace_all=true)
@Kif BEFORE
primaryColor: Colors.blue
@Kif END_BEFORE
@Kif AFTER
primaryColor: Color(0xFF6200EE)
@Kif END_AFTER
@Kif END_SEARCH_AND_REPLACE
```
```

---

## Remember

✅ **DO:**
- Always inquiry first, execute second
- Wait for inquiry results before writing execution
- **Always wrap KifDiff content in code blocks** (```kifdiff ... ```)
- Use absolute paths
- Write minimal, targeted changes
- Use regex when patterns are needed

❌ **DON'T:**
- Combine inquiry and execution in one response
- Make changes without examining the code first
- Use relative paths
- Rewrite entire files when small changes suffice
- Forget `replace_all=true` when using regex to replace all matches

---

**The golden rule:** If you haven't seen the inquiry results, you cannot write the execution file!