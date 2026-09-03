---
description: Create a GitHub pull request with full Mammoth Growth PR template
allowed-tools: Bash(git*), Bash(gh*)
---

# /github-create-pr

Push the current branch and create a GitHub PR using the Mammoth Growth PR template.

## Usage
/github-create-pr $ARGUMENTS

Where $ARGUMENTS is an optional PR title override.

## Pre-Requisites
- GitHub CLI (gh) must be installed and authenticated
- All changes must be committed
- Branch must be pushed to remote

## Steps

1. **Verify clean state**
   - Run: `git status`
   - If uncommitted changes exist, run /git-commit-all first

2. **Push branch**
   - Run: `git push origin $(git branch --show-current)`

3. **Gather PR content**
   Read the following to build the PR body:
   - The tech spec ($ARGUMENTS or most recently used spec)
   - Git log since branching from main: `git log main..HEAD --oneline`
   - List of files changed: `git diff --name-only main`

4. **Create PR using template**
   Fill in .claude/templates/pr-template.md with:
   - Requirements addressed (from tech spec)
   - Models built (from git diff)
   - Tests run and status (from last dbt build output)
   - Due diligence checklist (all items checked)

5. **Submit PR**
   - Run: `gh pr create --title "[title]" --body "[filled template]"`

6. **Confirm**
   Print the PR URL.
