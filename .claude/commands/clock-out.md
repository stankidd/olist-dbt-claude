---
description: End a work session cleanly - save context, commit WIP, and write a handoff note
allowed-tools: Read(*), Edit(*), Bash(git*)
---

# /clock-out

End a Claude Code session cleanly. Saves context, commits any
work-in-progress, and writes a handoff note for the next session.

## Steps

1. **Check git status**
   - Run: `git status`
   - List all uncommitted changes

2. **Commit work in progress** (if any)
   - Stage all changes: `git add -A`
   - Commit with WIP message: `git commit -m "WIP: [brief description of where things stand]"`

3. **Write handoff note**
   Create or update `plans/handoff.md` with:
   - What was completed this session
   - What is in progress (WIP commit details)
   - What comes next (next steps in order)
   - Any blockers or decisions needed
   - Which tech spec section is currently being worked on

4. **Save context summary**
   Append to `plans/session-log.md`:
   - Date and time
   - Models built or changed
   - Tests status
   - Decisions made

5. **Confirm**
   Print: "Session saved. Handoff note written to plans/handoff.md"
