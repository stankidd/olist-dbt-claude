---
description: Create a git commit for specific files with a descriptive message
allowed-tools: Bash(git*)
---

# /git-commit

Stage specific files and create a git commit.

## Usage
/git-commit $ARGUMENTS

Where $ARGUMENTS is a file path, glob, or commit description.

## Steps

1. **Review what will be committed**
   - Run: `git status`
   - If $ARGUMENTS is a path: `git diff $ARGUMENTS`

2. **Stage the specified files**
   - Run: `git add $ARGUMENTS`
   - Or if no files specified: `git add -A`

3. **Write commit message**
   Based on the staged changes, write:
   ```
   [type]: brief description

   Models changed: model_a, model_b
   Tests: all passing
   ```

4. **Commit**
   - Run: `git commit -m "[message]"`

5. **Confirm**
   Show commit hash and files committed.
