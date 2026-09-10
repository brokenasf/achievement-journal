# Contributing

Useful contributions include reproducible bug fixes, accessibility improvements, clearer Russian copy and corrections to achievement criteria with sources. Please discuss substantial features before implementing them; the project intentionally has no server or account system.

## Local checks

```sh
node --test tests/*.test.mjs
python -m unittest discover -s tests -p "test_*.py"
node scripts/serve.mjs
```

Test affected interactions using a disposable local journal. Check keyboard access, mobile layouts, persistence and backup recovery when relevant. Never attach your token or a private journal to an issue.

## Pull requests

Keep each PR focused on one real improvement. Describe the problem, resulting behavior and checks performed. CI must pass. A screenshot helps for visual changes. Do not create empty or duplicate changes for achievement counters.

For real collaborative work, record the contributor's agreed GitHub-associated name and email in a `Co-authored-by: Name <email>` commit trailer and preserve it on merge. Do not invent contributors or copy someone else's email without their participation. AI assistance is not proof of a second human coauthor.

## Suitable first collaboration

A useful bounded contribution is a native-speaker review of Russian accessibility announcements, tested with a screen reader. Another is a reproducible import edge case with a minimal fixture. Open an issue describing the finding before proposing the fix.
