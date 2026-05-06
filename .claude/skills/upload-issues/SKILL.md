---
name: upload-issues
description: Upload issues from a phase issues file to GitHub one by one with proper labels and dependencies.
---

# Skill: Upload Phase Issues to GitHub

Upload issues from a phase issues file to GitHub one by one, with proper labels and dependencies.

## Usage

```
/upload-issues <phase-issues-file>
```

Example: `/upload-issues @specifications/roadmap/phase-1-issues.md`

## Instructions

### Step 1: Read the phase issues file

Read the provided phase issues file (e.g., `specifications/roadmap/phase-{N}-issues.md`).

Determine from the file path:
- **N** (phase number): from `phase-{N}-issues.md` (e.g., `phase-1-issues.md` → N = `1`)
- **Label prefix**: `phase:{N}` (e.g., `phase:1`)

Parse the **Issues Summary Table** to extract for each issue:
- `ID` (e.g., TXP-001)
- `Title`
- `Size` (S, M, L)
- `Stage` (e.g., "1 — Data Models")
- `Dependencies` (list of TXP-xxx IDs)

Then parse each **detailed issue section** (## heading with TXP-xxx) to extract:
- `Description`
- `What needs to be done` (full content)
- `Dependencies`
- `Expected result`
- `Acceptance criteria` (checklist)

### Step 2: Confirm with user

Show the user a summary of what will be created:
- Number of issues
- Phase label (e.g., `phase:1`)
- Full list of labels that will be created
- Ask for confirmation before proceeding

### Step 3: Create labels (if they don't exist)

Use `gh` to create these labels if they don't already exist:

```bash
# Phase label
gh label create "phase:${N}" --color "0052CC" --description "Phase ${N}" 2>/dev/null || true

# Size labels
gh label create "size:S" --color "28A745" --description "Small (1-2 days)" 2>/dev/null || true
gh label create "size:M" --color "FFC107" --description "Medium (3-5 days)" 2>/dev/null || true
gh label create "size:L" --color "DC3545" --description "Large (5-8 days)" 2>/dev/null || true

# Stage labels (extract from issues)
gh label create "stage:Data Models" --color "6F42C1" 2>/dev/null || true
# ... etc for each unique stage found in the issues
```

### Step 4: Create issues ONE BY ONE

**IMPORTANT:** Issues must be created one at a time, sequentially. After creating each issue:
1. Show the user the result (issue number, URL)
2. Proceed to the next issue immediately (do not wait for confirmation between issues)

For each issue (in order from the summary table):

1. Build the issue body in markdown:

```markdown
## Description
{description from the detailed section}

## What needs to be done
{full content from the detailed section}

## Dependencies
{dependency list, with references to already-created issue numbers}

## Expected result
{expected result from the detailed section}

## Acceptance criteria
{checklist from the detailed section}

---
**ID:** {TXP-xxx}
**Size:** {S/M/L}
**Phase:** {N}
**Stage:** {stage name}
```

2. Create the issue with a single `gh issue create` command (one issue per command, never batch):

```bash
gh issue create \
  --title "TXP-xxx: {title}" \
  --label "phase:${N},size:{S/M/L},stage:{stage-name}" \
  --body "$(cat <<'BODY'
{issue body}
BODY
)"
```

3. Record the mapping: TXP-xxx -> GitHub issue #number

4. Report to user: `Created TXP-xxx → #{number}: {title}`

5. If the issue has dependencies on already-created issues, add a comment:

```bash
gh issue comment {issue-number} --body "Blocked by #{dep-issue-number} (TXP-xxx)"
```

6. Move to the next issue.

### Step 5: Generate report

After all issues are created, generate a report file at:
`specifications/roadmap/phase-{N}-github-report.md`

Content:

```markdown
# Phase {N} — GitHub Issues Report

**Uploaded:** {date}
**Repository:** {github repo URL}
**Total issues:** {count}

## Issue Mapping

| TXP ID | GitHub # | Title | Labels | URL |
|--------|----------|-------|--------|-----|
| TXP-001 | #1 | Protocol data models and status codes | phase:1, size:S, stage:Data Models | {url} |
| ... | ... | ... | ... | ... |

## Labels Created

- phase:{N}
- size:S, size:M, size:L
- stage:{list}
```

### Step 6: Report to user

Show the user:
- Total issues created
- Link to the GitHub issues page
- Path to the generated report file

## Error Handling

- If `gh` is not authenticated, tell the user to run `gh auth login`
- If an issue already exists with the same title, skip it and note in the report
- If label creation fails, continue (labels may already exist)
- On any failure, report what was created so far and what remains
