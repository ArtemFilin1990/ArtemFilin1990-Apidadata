---
name: read-fix-files
description: Use when user asks to read project files, find defects, and apply minimal safe fixes with tests and clean git history.
---

# Read & Fix Files

Use this skill when the request is about auditing repository files and correcting errors.

## Workflow

1. **Scope and constraints first**
   - Read task text and AGENTS.md instructions in scope.
   - Do not invent APIs, env vars, or endpoints.

2. **Find source of truth**
   - Read: `README*`, runtime entrypoints (`app.py`, `main.py`, etc.), config files, deployment descriptors, and tests.
   - Prefer existing contracts over assumptions.

3. **Plan minimal patch**
   - Change the smallest number of files.
   - Priorities: correctness → security → maintainability → performance.

4. **Apply safe fixes**
   - Keep behavior explicit (no hidden magic).
   - Validate inputs and avoid exposing secrets in logs or responses.
   - Preserve backward compatibility unless explicitly requested.

5. **Validate**
   - Run targeted tests first, then broader checks if needed.
   - For web services, run a smoke check for startup and `/health` when possible.

6. **Ship cleanly**
   - Commit with a focused message.
   - Ensure `git status` is clean.
   - Include rollback note if compatibility/runtime behavior changed.

## Standard command checklist

Run only what is relevant:

```bash
pytest -q
pytest -q tests/test_app_health.py tests/test_webhook.py
python -m py_compile app.py tg_bot.py config.py
```

## Iteration rule (continuous improvement)

After each run, refine this skill by adding:
- one recurring defect pattern found,
- one useful check command,
- one clarification that prevented a previous mistake.

Keep additions concise and practical.
