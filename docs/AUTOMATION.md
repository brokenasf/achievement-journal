# Python automation

The CLI automates delivery of real changes, not creation of artificial activity. It never creates empty PRs, stars repositories, invents coauthors or accepts discussion answers. GitHub decides when badges and tiers are awarded.

Requires Python 3.10+, Node.js 20+ and Git. It uses only the Python standard library. Run commands from the repository root. Supply a repository-scoped GitHub token using `GITHUB_TOKEN` or the ignored `token.txt` file. It needs access to repository contents, PRs and read access to checks; workflow changes additionally need permission to update workflows. Do not put tokens in command arguments.

## Read progress

```sh
python scripts/achievements.py status
```

Writes `.artifacts/progress.json`: visible merged PR count, stars on this repository, estimated tiers and distance to the next threshold. Counts do not prove a badge has appeared. Confirm badges on the linked profile page. Private activity is visible only to the extent permitted by the token.

## Publish one prepared change

Write the PR description in a UTF-8 file, such as `.artifacts/change.md`. Prepare the code changes and explicitly name the files to stage:

```sh
python scripts/achievements.py publish --branch fix/example --title "Describe the real fix" --body-file .artifacts/change.md --paths dist/app.js tests/model.test.mjs --merge
```

Without `--merge`, the tool only opens a PR. With `--merge`, it waits up to 10 minutes for the `test` check and any other reported checks, then asks GitHub to merge the exact checked commit. It never disables branch protection. Use `--timeout 1200` before the subcommand to extend the wait. Additional required checks can be named using `--required-check NAME`.

The token owner and HTTPS origin must match `--repo` (default `brokenasf/achievement-journal`). The index must initially be empty. Only explicitly selected paths are staged; credential files, symlinks and files containing the supplied token are rejected. This is a targeted guard, not a general-purpose secret scanner.

## Process a queue

Prepare independent changes in separate files on `main`. Create an ignored `.artifacts/queue.json`:

```json
[
  {"branch":"docs/usage","title":"Document backup recovery","body_file":".artifacts/usage.md","paths":["docs/USAGE.md"]},
  {"branch":"test/recovery","title":"Test backup recovery","body_file":".artifacts/recovery.md","paths":["tests/recovery.test.mjs"]}
]
```

```sh
python scripts/achievements.py queue --file .artifacts/queue.json --merge
```

Each item runs local Node/Python tests, commits its files, pushes, opens a PR, waits for CI and merges before starting the next. Prepare independent changes; local tests see the entire working directory, while CI tests only each committed snapshot. Do not use queue items that depend on uncommitted changes from later items.

On a failure, processing stops and leaves the PR or branch available for inspection. Repeating the same command reuses the existing PR instead of creating a duplicate; already merged items are skipped. A failed or changed PR must be repaired and pushed before retrying. If interrupted after merging but before returning to `main`, switch to `main` and pull before continuing the queue. Merge events are recorded in `.artifacts/automation-events.jsonl`.

No recurring background job is installed. One invocation handles the prepared queue and exits.
