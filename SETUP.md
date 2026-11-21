# Setup (5 minutes)

1. Your profile repo must be named exactly `mabdullahab614-alt/mabdullahab614-alt`.
2. Copy everything in this folder into that repo (`README.md`, `assets/`, `scripts/`, `.github/`).
3. For live data: create a classic Personal Access Token (scope: `read:user`), save it as a repo secret named `PROFILE_TOKEN`
   (Settings > Secrets and variables > Actions). Without it the workflow falls back to the built-in token, which only sees public data.
4. Actions tab > "Generate profile animations" > Run workflow. After that it refreshes every 6 hours.
5. Preview locally with fake data: `python scripts/generate.py --demo`
