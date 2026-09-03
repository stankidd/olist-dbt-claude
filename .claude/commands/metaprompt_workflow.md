---
description: Generate an optimized prompt for a complex agentic task using meta-prompting
allowed-tools: Read(*)
---

# /metaprompt-workflow

Use meta-prompting to generate the best possible prompt for a complex task
before executing it. This improves agent output quality on ambiguous or
high-stakes tasks.

## Usage
/metaprompt-workflow $ARGUMENTS

Where $ARGUMENTS describes the task you want to accomplish.

## When to Use This
Use this command when:
- The task is complex or ambiguous
- A poor prompt would waste significant compute
- You want to validate your approach before a long agentic run
- You are designing a new skill or command

## Steps

1. **Analyze the task**
   Given: $ARGUMENTS
   Identify:
   - What is the desired output?
   - What context is needed?
   - What skills/tools are required?
   - What are the failure modes?

2. **Generate optimized prompt**
   Write a prompt that:
   - Has a clear role definition ("You are a Mammoth Growth analytics engineer...")
   - Specifies exact steps in order
   - Includes validation criteria
   - References the correct skills and tools
   - Handles edge cases explicitly

3. **Review and refine**
   - Show the generated prompt
   - Explain why each section is worded that way
   - Ask for approval before executing

4. **Execute** (if approved)
   Run the optimized prompt as the actual task.
