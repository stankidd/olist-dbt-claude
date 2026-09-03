---
description: Stage and commit all current changes with a descriptive commit message
allowed-tools: Bash(git*)
---

# /git-commit-all

Stage all current changes and create a well-formatted git commit.

## Usage
/git-commit-all $ARGUMENTS

Where $ARGUMENTS is an optional commit message.
If not provided, Claude will generate one from the changes.

## Steps

1. **Review changes**
   - Run: `git status`
   - Run: `git diff --stat`
   - Understand what files changed and why

2. **Generate commit message** (if not provided)
   Based on the changes, write a commit message following this format:
   ```
   [type]: brief description (max 72 chars)

   - Detail 1
   - Detail 2
   ```
   Types: feat, fix, docs, style, refactor, test, chore

3. **Stage and commit**
   - Run: `git add -A`
   - Run: `git commit -m "[generated or provided message]"`

4. **Confirm**
   Show the commit hash and message.
