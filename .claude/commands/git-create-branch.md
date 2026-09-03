---
description: Create a new git branch following Mammoth naming conventions
allowed-tools: Bash(git*)
---

# /git-create-branch

Create a new feature branch following Mammoth Growth naming conventions.

## Usage
/git-create-branch $ARGUMENTS

Where $ARGUMENTS is the use case or feature name.
Example: /git-create-branch forecasting-model

## Naming Convention
Mammoth branch names follow this format:
`
initials/use-case-name
`
Example: dc/forecasting-model

## Steps

1. **Determine branch name**
   - Read CLAUDE.md for the engineer's initials (or ask if not set)
   - Combine with the argument provided: initials/your-feature-name
   - Replace spaces with hyphens, lowercase everything

2. **Check current branch**
   - Run: git branch --show-current
   - If not on main/master, confirm before branching

3. **Pull latest**
   - Run: git pull origin main

4. **Create branch**
   - Run: git checkout -b initials/your-feature-name

5. **Confirm**
   Print the new branch name that was created.
