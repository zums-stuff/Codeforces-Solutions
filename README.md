# 🚀 Codeforces Submissions Auto-Sync

Automatically **fetch and sync your accepted Codeforces submissions** into this repository using **GitHub Actions** — zero manual copy-paste.

![GitHub Actions](https://img.shields.io/github/actions/workflow/status/YOUR_GITHUB_USERNAME/YOUR_REPO/codeforces_commit.yml?label=Auto-Sync&logo=github&style=for-the-badge)
![Codeforces](https://img.shields.io/badge/Codeforces-Automation-blue?logo=codeforces&style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-lightgrey?style=for-the-badge)

> Replace `YOUR_GITHUB_USERNAME/YOUR_REPO` above with your repo path.

---

## ✨ What this does

- 🔎 Tracks your **latest Accepted (AC)** submissions from Codeforces.
- 📁 Saves each solution under `submissions/`, grouped by problem ID (e.g., `1700_A.cpp`).
- ⏱️ Runs **every 15 minutes** (and supports manual runs).
- 🧠 Avoids duplicates with a lightweight `submission_history.json`.
- 🧰 Language-agnostic: **C++ / Python / Java / more** — stored with the right file extension.

---

## ⚙️ How it works

1. A scheduled GitHub Action triggers every 15 minutes.
2. The script queries the **Codeforces API** for your most recent **AC** submissions.
3. New solutions are:
   - written to `submissions/<problem_id>.<ext>`
   - committed and pushed to the repo
4. A local history file ensures the same submission isn’t pushed twice.

---

## 🔧 Setup

### 1) Fork this repository
Click **Fork** to create your copy.

### 2) Add a GitHub token (repo write access)
1. Go to **Settings → Secrets and variables → Actions**  
2. Click **New repository secret**  
3. **Name:** `GH_TOKEN`  
4. **Value:** your **GitHub Personal Access Token** with **repo** (read/write) scope

> Tip: A classic token with `repo` permissions is sufficient for private or public repos.

### 3) Set your Codeforces handle
Open `.github/workflows/codeforces_commit.yml` and set:
```yaml
env:
  CF_HANDLE: your_codeforces_handle
```
Commit the change.

> Prefer keeping secrets out of YAML? You can also store the handle as an **Actions variable** (`Settings → Secrets and variables → Actions → Variables`) and reference it with `${{ vars.CF_HANDLE }}`.

---

## ▶️ Usage

- **Automatic**: runs every 15 minutes by default.
- **Manual**:
  1. Go to **Actions** tab
  2. Select **Codeforces Auto-Sync**
  3. Click **Run workflow**

---

## 📁 Repository Structure

```txt
📦 your-repo
├─ 📂 submissions/
│  ├─ 1700_A.cpp
│  ├─ 1805_B.py
│  └─ 1866_C.java
├─ submission_history.json
├─ .github/
│  └─ workflows/
│     └─ codeforces_commit.yml
└─ README.md
```

- **`submissions/`** → All accepted solutions (organized by problem ID).  
- **`submission_history.json`** → Simple ledger to avoid duplicate commits.  
- **`codeforces_commit.yml`** → The GitHub Actions workflow.

---

## 🧩 Customization

- **Schedule cadence**: edit the cron in `codeforces_commit.yml`:
```yaml
on:
  schedule:
    - cron: "*/15 * * * *"  # every 15 minutes
```

- **Branch target**:
```yaml
env:
  TARGET_BRANCH: main  # or 'master' / any branch you prefer
```

- **File naming**: tweak naming logic in the script (e.g., include contest ID, problem index, or submission ID).

---

## ❓ FAQ / Troubleshooting

- **No files are syncing**
  - Check **Actions → Codeforces Auto-Sync** logs.
  - Verify `CF_HANDLE` is correct and **public** on Codeforces.
  - Ensure your token in `GH_TOKEN` has **write** permissions.

- **“Permission denied” on push**
  - Confirm the secret is named exactly `GH_TOKEN`.
  - Token must have **repo** scope and not be expired/revoked.

- **Wrong file extension**
  - Mapping uses Codeforces language → extension rules. Adjust the script if you prefer different extensions.

---

## 🤝 Contributing

Have an idea or found a bug? Fork the repo, open a PR, or start a discussion. Thoughtful improvements are welcome.

---

## 📜 License

This project is released under the **MIT License**. See `LICENSE` for details.

---

> Pro tip: Pin this repo on your GitHub profile so your Codeforces progress is always visible and versioned.
