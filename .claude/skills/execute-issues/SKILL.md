---
name: execute-issues
description: Execute GitHub issues for a phase sequentially - implement, validate, commit, push, and generate a report.
---

# Skill: Execute GitHub Issues

Execute GitHub issues for a phase sequentially: implement, validate, commit, push, and generate a report.

## Usage

```
/execute-issues <phase> [--issue TXP-xxx] [--dry-run]
```

The `<phase>` is the phase number (e.g., `1`).

- `/execute-issues 1` — execute all issues for phase 1
- `/execute-issues 1 --issue TXP-003` — execute a single issue from that phase
- `/execute-issues 1 --dry-run` — show execution plan without making changes

## Instructions

### Step 0: Verify prerequisites

1. Confirm we are on the `main` branch (or the user's working branch)
2. Confirm working tree is clean (`git status`)
3. Confirm `gh` is authenticated
4. Parse the phase number from the argument
5. Fetch issues from GitHub:
   ```bash
   gh issue list --label "phase:{N}" --state open --limit 100
   ```
6. Read the phase issues file for detailed descriptions: `specifications/roadmap/phase-{N}-issues.md`
7. Read the phase tasks file: `specifications/roadmap/phase-{N}-tasks.md`
8. If a GitHub report exists (`phase-{N}-github-report.md`), read the TXP-to-GitHub# mapping

### Step 1: Build execution queue

From the GitHub issue list, build an ordered queue based on dependencies:
- Parse TXP-xxx IDs from issue titles (format: `TXP-xxx: {title}`)
- Determine dependency order from the phase issues file dependency tree
- Issues with no unmet dependencies go first
- Skip issues already closed on GitHub
- If `--issue TXP-xxx` is specified, execute only that issue (but verify its dependencies are closed)

Show the user the execution plan and ask for confirmation.

### Step 2: Execute each issue (loop)

For each issue in the queue:

#### 2a. Assign and announce

```bash
gh issue edit {issue-number} --add-assignee "@me"
```

Print: `--- Starting TXP-xxx: {title} ---`

#### 2b. Read issue details

Read the full issue description from the phase issues file (the detailed section for this TXP-xxx). Also read all related tasks from the phase tasks file (tasks referencing this TXP-xxx in the Issue column).

#### 2c. Implement

Execute the tasks described in the issue. Follow the architecture in `specifications/ARCHITECTURE.md` and the specification in `specifications/TXP-Server-Specification-EN.md`. Key rules:

- Create files in the locations specified by the architecture
- Follow existing code style and patterns from already-implemented modules
- Write tests alongside implementation when the issue includes test tasks
- Use Python 3.11+ features, stdlib-only (no external dependencies until Phase 3)

#### 2d. Validate

Run validation checks:

1. **Syntax check:** `python -m py_compile {changed_files}` for each new/modified .py file
2. **Import check:** `python -c "import {module}"` for each new module
3. **Tests:** `pytest -x --tb=short` if tests exist
4. **Acceptance criteria:** go through each criterion from the issue and verify

Record pass/fail for each check.

#### 2e. Commit

```bash
git add {specific files created/modified}
git commit -m "$(cat <<'EOF'
TXP-xxx: {title}

{1-2 sentence summary of what was implemented}

Closes #{github-issue-number}

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

#### 2f. Push

```bash
git push
```

#### 2g. Close issue with summary

```bash
gh issue close {issue-number} --comment "$(cat <<'EOF'
## Implementation Summary

**Commit:** {commit-hash}
**Files changed:** {count}

### What was done
{bullet list of key changes}

### Validation
{pass/fail status for each check}

### Acceptance criteria
{checklist with pass/fail}
EOF
)"
```

#### 2h. Log progress

Append to the in-memory execution log:
- Issue ID, title
- Commit hash
- Files changed (list)
- Validation results
- Status: success/partial/failed

### Step 3: Handle failures

If implementation or validation fails for an issue:

1. Do NOT commit broken code
2. Stash or revert changes: `git checkout -- .`
3. Add a comment to the GitHub issue explaining what failed
4. Log the failure
5. Ask the user: continue to next issue (if no dependency), or stop?

### Step 4: Generate execution report

After all issues are processed (or on stop), generate:
`specifications/roadmap/phase-{N}-execution-report.md`

```markdown
# Phase {N} — Execution Report

**Date:** {date}
**Branch:** {branch name}
**Phase:** {N}
**Executed by:** Claude Code

## Summary

| Status | Count |
|--------|-------|
| Completed | {n} |
| Failed | {n} |
| Skipped | {n} |
| Remaining | {n} |

## Issues

| # | TXP ID | Title | Status | Commit | Files | Tests |
|---|--------|-------|--------|--------|-------|-------|
| 1 | TXP-001 | Protocol data models and status codes | completed | a1b2c3d | 5 | 0/0 |
| 2 | TXP-002 | Header parsing and serialization | completed | e4f5g6h | 2 | 3/3 |
| ... | ... | ... | ... | ... | ... | ... |

## Detailed Results

### TXP-001: Protocol data models and status codes

**Status:** completed
**Commit:** a1b2c3d
**Files changed:**
- `protocol/__init__.py` (new)
- `protocol/status.py` (new)
- ...

**Validation:**
- [x] Syntax check: all files pass
- [x] Import check: all modules import
- [ ] Tests: N/A (no tests yet)
- [x] Acceptance criteria: 6/6 pass

---

### TXP-002: Header parsing and serialization
...

## Next Steps

{List of remaining issues not yet executed, with their dependencies}
```

Commit and push this report:

```bash
git add specifications/roadmap/phase-{N}-execution-report.md
git commit -m "$(cat <<'EOF'
Add phase {N} execution report

{n} issues completed, {n} failed, {n} remaining.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
git push
```

## Important Rules

- **One issue at a time.** Never work on multiple issues simultaneously.
- **Dependency order.** Never start an issue whose dependencies are not closed.
- **Clean commits.** Each issue = one commit. No mixing work across issues.
- **No broken code.** Only commit code that passes validation.
- **Ask on ambiguity.** If an issue description is unclear, ask the user rather than guessing.
- **Progress updates.** Print a short status line after each issue completes.
