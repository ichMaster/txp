---
name: release-version
description: Bump project version, update all version files, add CHANGELOG entry, commit, tag, and push.
---

# Skill: Release Version

Bump the project version, update all version references, write release notes, commit, tag, and push.

## Usage

```
/release-version <version> [changelog line 1] [changelog line 2] ...
```

Examples:
- `/release-version 0.1.0` — bump to 0.1.0, prompt for changelog
- `/release-version 0.2.0 Add protocol layer; Add request parser` — bump with provided changelog items

If no changelog items are provided, analyze uncommitted or recent commits since the last tag to auto-generate the changelog.

## Instructions

### Step 0: Parse arguments

1. Extract the target version from the first argument (e.g., `0.1.0`)
2. Remaining arguments (separated by `;`) become changelog bullet points
3. Validate version format matches `X.Y.Z` (semver)

### Step 1: Verify prerequisites

1. Confirm we are on the expected branch (`main` or user's working branch)
2. Confirm working tree is clean (`git status`) — if dirty, ask the user whether to include uncommitted changes
3. Determine the current version:
   - Check `pyproject.toml` if it exists
   - Check for the latest git tag: `git describe --tags --abbrev=0 2>/dev/null`
   - If no version exists yet, treat current as `0.0.0`
4. Verify the new version is greater than the current version

### Step 2: Generate changelog (if not provided)

If no changelog items were given as arguments:

1. Find the most recent version tag: `git describe --tags --abbrev=0`
2. Collect commits since that tag: `git log --oneline <tag>..HEAD`
3. If no tags exist, collect all commits: `git log --oneline`
4. Summarize the changes into concise bullet points (group related commits)
5. Show the generated changelog to the user and ask for confirmation

### Step 3: Update version files

Update the version string in these files (create if they don't exist):

1. **`pyproject.toml`** (if it exists):
   ```toml
   version = "<version>"
   ```

2. **`txp_server.py`** (if it exists):
   - Update or add `__version__ = "<version>"` near the top of the file

3. **`README.md`** (if it has a version line):
   - Update `**Version:** X.Y.Z` line if present

### Step 4: Add CHANGELOG entry

Prepend a new version block at the top of `CHANGELOG.md` (create if it doesn't exist). If creating, add a header first:

```markdown
# Changelog

## Version <version> (YYYY-MM-DD)

- <changelog item 1>
- <changelog item 2>
- ...
```

If the file already exists, prepend the new version block after the `# Changelog` header. Use today's date. Keep the existing entries below unchanged.

### Step 5: Commit

Stage only the version-related files:

```bash
git add pyproject.toml txp_server.py README.md CHANGELOG.md
```

Only add files that actually exist and were modified. Commit with message:

```bash
git commit -m "$(cat <<'EOF'
Release v<version>

<1-2 sentence summary of what this release includes>

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

### Step 6: Tag

Create an annotated tag:

```bash
git tag -a v<version> -m "<one-line summary of the release>"
```

### Step 7: Push

```bash
git push && git push --tags
```

### Step 8: Report

Print a summary:

```
Released v<version>
  Branch: <branch>
  Commit: <short hash>
  Tag:    v<version>
  Files updated:
    - <list of files that were modified>
```

## Important Rules

- **Never downgrade.** Refuse if the target version is less than or equal to the current version.
- **Clean tree first.** If there are uncommitted changes, ask the user before proceeding.
- **Annotated tags only.** Always use `git tag -a`, never lightweight tags.
- **Don't modify other files.** This skill only touches version metadata, not source code.
- **Confirm changelog.** If auto-generating changelog from commits, show it to the user before committing.
