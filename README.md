# Achievement Journal

A small, local-first journal for GitHub achievements. Russian interface, no account, token or server required.

This project records progress manually. It does not unlock achievements or automatically verify GitHub activity.

## Development

Requires Node.js 20 or newer. No dependencies to install.

```sh
npm start
npm test
```

Open http://127.0.0.1:4173. Public site files live in `dist/`.

## Automate the contribution workflow

The [Python CLI](docs/AUTOMATION.md) checks changes, opens PRs, waits for CI, optionally merges them and reports achievement tier estimates. It supports a queue of prepared changes and resumes existing PRs. It uses no third-party Python dependencies and never creates empty contributions.

```sh
python scripts/achievements.py status
python -m unittest discover -s tests -p "test_*.py"
```
