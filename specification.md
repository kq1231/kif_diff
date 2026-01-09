### 1. The KifDiff Language Specification

A `.kifdiff` file is a plain text file that contains one or more operations. Each operation is defined by a set of directives.

**Directives:**
*   `@Kif FILE <file_path>`: Specifies the target file for all subsequent operations until the next `@Kif FILE` directive.
*   `@Kif CREATE`: A block directive to create a new file.
*   `@Kif DELETE`: A standalone directive to delete a file.
*   `@Kif SEARCH_AND_REPLACE`: A block directive to perform a search and replace.

---

#### Tool 1: Create File

Creates a new file with the specified content. If the file already exists, it will be overwritten.

**Syntax:**

```
@Kif FILE <path/to/new_file.txt>
@Kif CREATE
... (file content goes here) ...
@Kif END_CREATE
```

**Example:**
To create a new Dart file `lib/constants.dart`:

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

#### Tool 2: Delete File

Deletes the specified file from the filesystem.

**Syntax:**

```
@Kif FILE <path/to/file_to_delete.txt>
@Kif DELETE
```

**Example:**
To delete an old utility file `lib/old_utils.dart`:

```
@Kif FILE lib/old_utils.dart
@Kif DELETE
```

---

#### Tool 3: Search and Replace

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

**Example:**
Let's use this to add a new section to your `app_bar_demo_page.dart`. This is the exact operation you were trying to do with the git patch.

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
              code: '''
UIAppBar(
  title: 'Messages',
  showMenuButton: true,
  actions: [
    IconButton(
      icon: Icon(Icons.search),
      onPressed: () {},
    ),
    IconButton(
      icon: Icon(Icons.more_vert),
      onPressed: () {},
    ),
  ],
)''',
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 16),
                  _buildAppBarPreview(
                    UIAppBar(
                      title: 'Messages',
                      showMenuButton: true,
                      actions: [
                        IconButton(
                          icon: const Icon(Icons.search),
                          onPressed: () {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text('Search pressed')),
                            );
                          },
                        ),
                        IconButton(
                          icon: const Icon(Icons.more_vert),
                          onPressed: () {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text('More pressed')),
                            );
                          },
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Section: With Title Tap
@Kif END_AFTER
@Kif END_SEARCH_AND_REPLACE
```