# Push this repository to GitHub

Suggested destination:

```text
https://github.com/bmsull560/fcc-router-consumer-awareness
```

## Option A: GitHub CLI

From the unzipped repository folder:

```bash
gh auth login
gh repo create bmsull560/fcc-router-consumer-awareness --public --source=. --remote=origin --push
```

Use `--private` instead of `--public` if you want a private repo.

## Option B: GitHub website + git

1. Create a new empty repository at GitHub named `fcc-router-consumer-awareness` under `bmsull560`.
2. Do not initialize it with a README, license, or `.gitignore`.
3. From this folder, run:

```bash
git remote add origin https://github.com/bmsull560/fcc-router-consumer-awareness.git
git branch -M main
git push -u origin main
```

SSH alternative:

```bash
git remote add origin git@github.com:bmsull560/fcc-router-consumer-awareness.git
git branch -M main
git push -u origin main
```
