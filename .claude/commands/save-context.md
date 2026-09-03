---
description: Save current session context and progress to a file for future reference
allowed-tools: Read(*), Edit(*), Bash(git*)
---

# /save-context

Save a snapshot of the current session's progress, decisions, and state
to plans/session-context.md for future sessions or handoffs.

## Usage
/save-context $ARGUMENTS

Where $ARGUMENTS is an optional label for this context snapshot.

## Steps

1. **Gather current state**
   - Run: `git status` -- what files have changed?
   - Run: `git log --oneline -10` -- what was recently committed?
   - Run: `dbt ls` -- what models currently exist?

2. **Document progress**
   Write to plans/session-context.md (create if not exists, append if exists):

   ```markdown
   ## Session: [date/time] -- $ARGUMENTS

   ### Completed
   - [list models built and committed]

   ### In Progress
   - [current model being worked on]
   - [current state / where things stand]

   ### Next Steps
   - [ordered list of what comes next]

   ### Decisions Made
   - [any non-obvious choices made and why]

   ### Tech Spec Reference
   - File: [path to tech spec]
   - Section: [current section]
   ```

3. **Confirm**
   Print: "Context saved to plans/session-context.md"
   Print a summary of what was saved.
