# Git Workflow — Keep Repo Clean & Portable

Goal: at any moment you can clone/pull this repo on another PC (e.g. at work) and get a clean, usable checkout.

Rules of thumb:
- Keep `main` stable and clean (no local uncommitted changes on `main`).
- Do all work on a branch (`feature/...` for ready work, `wip/...` for in-progress work).
- Push your branch to GitHub so you can continue from another machine.
- Generated artifacts must stay out of git (`.venv/`, `__pycache__/`, logs, backups, etc.).

## Step 1: Create and Switch to a New Branch

```powershell
Set-Location 'C:\Users\AngelAdrian\Desktop\Acces\ZKAccessB'
git status
# You should see a clean working tree on main (recommended)

# Create a branch for your work
git checkout -b wip/office-sync-YYYY-MM-DD
```

## Step 2: Review Changes (Optional but Recommended)

```powershell
# See all changes
git diff

# See summary of changes
git status

# Show only filenames
git diff --name-only
```

## Step 3: Stage All Changes

```powershell
git add -A
```

## Step 4: Commit with a Descriptive Message

```powershell
git commit -m "port(commands+ci+db): modernize management commands, expand tests, improve CI, add DB migration plan

- Ported 5 management commands (worktable, iclock) from Python 2 to Python 3
- Added 3 test modules with 6 passing tests
- Improved CI workflow with caching and explicit Python runners
- Created comprehensive DB migration plan and runbook
- Added legacy code inventory and prioritized porting roadmap"
```

## Step 5: Push Branch to Remote (So You Can Continue Elsewhere)

```powershell
git push -u origin wip/office-sync-YYYY-MM-DD

# On another PC:
# git clone <repo_url>
# git checkout wip/office-sync-YYYY-MM-DD
```

## Step 6: Open PR on GitHub (When Ready)

Go to your repository on GitHub (https://github.com/YOUR_OWNER/ZKAccessB):
1. Click "Compare & pull request" (GitHub will show a prompt after pushing)
2. Or click "Branches" and then "New pull request" for the branch
3. Set base to `main` (or `master` if that's your default)
4. Set compare to your branch (e.g. `feature/...`)
5. Add a clear description of what changed and how to test
6. Click "Create pull request"

## Step 7: Code Review & Merge

- Assign reviewers
- Address any comments
- Once approved, click "Squash and merge" or "Create a merge commit" (per your workflow)

## Verification Commands (After Pushing)

```powershell
# Verify the branch exists remotely
git branch -r

# Show the latest commits on the branch
git log --oneline -10 wip/office-sync-YYYY-MM-DD

# Compare to main
git log --oneline main..wip/office-sync-YYYY-MM-DD
```

## If You Need to Make Additional Changes

```powershell
# Make your changes locally
# Then stage and commit:
git add -A
git commit -m "fix: additional improvements"

# Push again (no need for -u, already tracking remote)
git push
```

## If You Need to Undo and Start Over

```powershell
# Discard all local changes (BE CAREFUL)
git reset --hard HEAD

# Or switch back to main (recommended)
git checkout main
```

## Quick Git Cheat Sheet for This Workflow

| Command | Purpose |
|---------|---------|
| `git checkout -b wip/office-sync-YYYY-MM-DD` | Create and switch to new WIP branch |
| `git status` | See what's changed |
| `git diff` | See detailed changes |
| `git add -A` | Stage all changes |
| `git commit -m "message"` | Commit changes |
| `git push -u origin wip/office-sync-YYYY-MM-DD` | Push branch to remote |
| `git log --oneline -10` | View last 10 commits |
| `git branch -r` | List remote branches |

---

If `git status` is noisy, it usually means either:
- you’re on `main` with uncommitted changes (move work to a branch), or
- generated files are being created locally (add/verify `.gitignore`).
