---
name: prompt-response-logging
description: Logs each user prompt and a short summary of the agent's response to a project log file for presentations. Use when the user is developing a project and wants a chronological record of prompts and outcomes for demos or post-project presentations.
---

# Prompt & Response Logging

## Purpose

Keep a single project log of every user prompt and a brief summary of what was done or answered. The log is meant for use in a presentation after the project is complete.

## When to Log

- **Do log:** Every substantive user prompt and your response summary during project development in this workspace.
- **Skip logging:** If the user explicitly asks not to log (e.g. "don't log this"), or for meta/off-topic messages that are not about the project.

## Log File

- **Path:** `PROMPT_LOG.md` at the project root.
- Create the file if it does not exist; otherwise append one new entry per user prompt.

## Entry Format

Append exactly one block per prompt. Use this structure:

```markdown
---

### [Date – short prompt summary]

**Prompt:**  
[User's exact prompt or a concise paraphrase if very long]

**Summary:**  
[1–3 sentences: what you did or the answer you gave. Focus on outcomes and changes.]
```

Use the current date in a clear format (e.g. `2025-03-06`). For "short prompt summary" use a few words that would work as a slide or section title (e.g. "Add login form", "Fix auth bug", "Explain MCP tools").

## Workflow

1. Answer the user's prompt as usual.
2. After your response, append one entry to `PROMPT_LOG.md` using the format above.
3. Keep the summary brief and presentation-ready (what was asked, what was delivered).

## Example Entry

```markdown
---

### 2025-03-06 – Add login form to dashboard

**Prompt:**  
Add a login form to the dashboard with email and password, and wire it to the auth API.

**Summary:**  
Added a `LoginForm` component with email/password fields and client-side validation, connected it to the existing auth API, and updated the dashboard route to show the form when the user is not authenticated.
```

## Tips

- **Summaries:** Write for someone reading the log later or presenting it (e.g. "Implemented X", "Fixed Y by …", "Explained Z").
- **Long prompts:** If the prompt is very long, use a short paraphrase in the entry and note "(summary)" or "(paraphrased)" so the log stays scannable.
- **Multiple actions:** If you did several things, list the main outcomes in 1–3 sentences rather than step-by-step detail.
