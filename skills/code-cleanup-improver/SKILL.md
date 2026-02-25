---
name: code-cleanup-improver
description: Use when user asks to clean up existing code, perform safe refactoring, reduce technical debt, and improve readability/structure while preserving external behavior and compatibility.
---

# Code Cleanup Improver

Use this skill when requests look like:
- «улучши код»
- «приведи в чистый вид»
- «сделай рефакторинг без изменения логики»
- "clean up this module"
- "refactor safely without breaking API"

## Outcome

Produce minimal, reversible, production-ready cleanup changes.

Priority order:
1. Correctness
2. Security
3. Maintainability
4. Performance

## Non-goals

- No unrequested feature work.
- No contract breaks (API shape, env names, CLI flags, DB schema) without explicit instruction.
- No broad rewrites when a small patch solves the problem.

## Workflow

1. **Read source of truth first**
   - Open `README*`, runtime entrypoints, config, tests, CI, deployment descriptors.
   - List protected contracts before editing.

2. **Plan minimal patch**
   - Touch the fewest files possible.
   - Prefer isolated, mechanical refactors over architecture redesign.
   - Keep each commit focused and reviewable.

3. **Apply safe cleanup**
   - Remove dead code and obvious duplication.
   - Improve naming, split long functions, simplify branching.
   - Make validation and error paths explicit.
   - Add/keep timeouts for external calls.
   - Avoid logging secrets or sensitive payloads.

4. **Protect behavior with tests**
   - Add/update targeted tests around changed logic.
   - Cover critical and boundary paths first.

5. **Verify**
   - Run relevant lint/test/smoke checks from the repo.
   - If environment blocks a check, report limitation and exact follow-up command.

6. **Ship**
   - Commit with clear message.
   - Ensure `git status` is clean.
   - If compatibility/data format changes, include MIGRATION and ROLLBACK notes.

## Refactoring checklist

- Behavior preserved unless explicitly requested otherwise.
- No swallowed exceptions or hidden side effects.
- Input validation present (type/length/format/allowlist where relevant).
- External integrations have timeouts; retries only for idempotent operations.
- Logs are useful and sanitized.
- Code is simpler to read than before.

## Suggested verification baseline

Use only commands that exist for the target repo:

```bash
pytest -q
python -m py_compile app.py tg_bot.py config.py
```
