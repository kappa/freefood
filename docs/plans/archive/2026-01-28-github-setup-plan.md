# FreeFood GitHub Setup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a public GitHub repository named `freefood`, add it as `origin`, and push the local `main` branch.

**Architecture:** Use the GitHub CLI (`gh`) to create the remote repository, then wire it to the local git repo and push `main`.

**Tech Stack:** Git, GitHub CLI (`gh`)

---

### Task 1: Verify Local Git State

**Files:**
- None

**Step 1: Confirm current branch**

Run:
```bash
git branch --show-current
```
Expected: `main`

**Step 2: Check working tree status**

Run:
```bash
git status -sb
```
Expected: No uncommitted changes (or explicitly confirm if there are any)

**Step 3: Confirm no existing `origin` remote**

Run:
```bash
git remote -v
```
Expected: Either empty or no `origin` listed

---

### Task 2: Create GitHub Repository

**Files:**
- None

**Step 1: Create repo via GitHub CLI**

Run:
```bash
gh repo create freefood --public --source . --remote origin
```
Expected: Repo created and `origin` set

**Step 2: Verify remote**

Run:
```bash
git remote -v
```
Expected: `origin` points to the new GitHub repo

**Step 3: Verify repo exists**

Run:
```bash
gh repo view freefood --web
```
Expected: Browser opens repo page

---

### Task 3: Push `main` to GitHub

**Files:**
- None

**Step 1: Push main**

Run:
```bash
git push -u origin main
```
Expected: Push succeeds and upstream is set

**Step 2: Verify branch on GitHub**

Run:
```bash
gh repo view freefood --json name,defaultBranchRef,url
```
Expected: `defaultBranchRef` shows `main`

---

### Task 4: Optional Defaults (If Desired)

**Files:**
- None

**Step 1: Set repository description**

Run:
```bash
gh repo edit freefood --description "Console client for FreeFeed.net"
```
Expected: Description updated

**Step 2: Enable GitHub Actions**

Run:
```bash
gh repo edit freefood --enable-issues=false --enable-projects=false --enable-wiki=false
```
Expected: Repo settings updated (optional)

---

## Summary

After completing all tasks:
1. A public GitHub repository named `freefood` exists
2. Local `origin` points to the repo
3. `main` is pushed and set as default
