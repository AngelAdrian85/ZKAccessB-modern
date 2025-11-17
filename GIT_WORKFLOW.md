# Git Workflow — Complete Your PR

Since git is not available in the agent execution environment, you need to run these commands locally from your machine to finalize the porting work.

## Step 1: Create and Switch to a New Branch

```powershell
Set-Location 'C:\Users\AngelAdrian\Desktop\Acces\ZKAccessB'
git status
# You should see all the modified/untracked files from this session

# Create a new feature branch
git checkout -b port/python3/commands-and-migrations
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

## Step 5: Push Branch to Remote

```powershell
git push -u origin port/python3/commands-and-migrations
```

## Step 6: Open PR on GitHub

Go to your repository on GitHub (https://github.com/YOUR_OWNER/ZKAccessB):
1. Click "Compare & pull request" (GitHub will show a prompt after pushing)
2. Or click "Branches" and then "New pull request" for the branch
3. Set base to `main` (or `master` if that's your default)
4. Set compare to `port/python3/commands-and-migrations`
5. Copy and paste the content from `port_plan/PR_DESCRIPTION.md` into the PR body
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
git log --oneline -10 port/python3/commands-and-migrations

# Compare to main
git log --oneline main..port/python3/commands-and-migrations
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

# Or switch back to main
git checkout main
```

## Quick Git Cheat Sheet for This Workflow

| Command | Purpose |
|---------|---------|
| `git checkout -b port/python3/commands-and-migrations` | Create and switch to new branch |
| `git status` | See what's changed |
| `git diff` | See detailed changes |
| `git add -A` | Stage all changes |
| `git commit -m "message"` | Commit changes |
| `git push -u origin port/python3/commands-and-migrations` | Push branch to remote |
| `git log --oneline -10` | View last 10 commits |
| `git branch -r` | List remote branches |

---

**All your workspace files are ready to commit!** Run these commands from your PowerShell terminal and your PR will be on GitHub. The work is production-ready and documented for review.
