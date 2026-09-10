# Using the journal

Open [the public demo](https://brokenasf.github.io/achievement-journal/). No sign-in is needed. All six achievements start at zero for each new browser or origin.

1. Enter the number of qualifying events in an achievement card. Progress targets the next threshold; the tier chips show thresholds you have already reached.
2. Open **Подтверждения** and add a GitHub link to a PR, issue, accepted discussion answer or repository. Adding evidence does not change the count automatically.
3. Check **Значок появился в профиле** only after seeing the badge on your GitHub profile. Counts and confirmation are deliberately independent.
4. Use **Экспорт JSON** to save a backup. Use **Импорт JSON** to select a backup, inspect the replacement warning and confirm. Cancel or Escape preserves your current journal.

## Storage and privacy

The app stores records under `achievement-journal:v1` in localStorage. It sends no journal records to a server and has no analytics or third-party asset requests. Hosting providers still receive normal page requests. Other pages sharing the same origin can access that origin's browser storage; avoid storing secrets in evidence URLs. GitHub Pages projects under the same account share an origin.

Different browsers, devices, localhost, GitHub Pages and other hosting origins keep separate journals. Transfer data using a JSON backup. Clearing site data deletes the browser copy. Private browsing or browser policies may prevent persistence.

If storage cannot be read, automatic saving is paused to preserve the original data. Importing a valid backup explicitly replaces it. If storage is full or denied, a warning remains visible: export your current work before closing the tab.

## Valid backup format

Version 1 contains an `entries` object with all six achievement IDs. Each entry has an integer `count` from 0 to 100,000,000, a boolean `confirmed`, and up to 100 distinct HTTPS GitHub evidence URLs. Files over 1 MB, invalid JSON and unsupported versions are rejected before any current data is replaced.

## What counts

| Achievement | Base / higher thresholds |
| --- | --- |
| Quickdraw | Close an issue or PR within 5 minutes |
| YOLO | Merge your own PR without code review |
| Pull Shark | 2 / 16 / 128 / 1024 merged PRs |
| Pair Extraordinaire | 1 / 10 / 24 / 48 coauthored merged PRs |
| Galaxy Brain | 2 / 8 / 16 / 32 accepted answers |
| Starstruck | 16 / 128 / 512 / 4096 stars on one repository |

These are community-observed criteria, not a GitHub guarantee. GitHub Community Discussions no longer awards achievements. See the [maintained catalog](https://github.com/Schweinepriester/github-profile-achievements) and [official profile reference](https://docs.github.com/en/account-and-profile/reference/profile-reference#earning-achievements). Badge delivery and search indexing can be delayed.
