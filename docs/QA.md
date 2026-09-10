# Validation record

Validated during initial implementation on 2026-09-10.

## Automated

- Eight Node tests cover tier boundaries, independent confirmations, backup round trips, URL safety, duplicate evidence, schema validation, storage corruption and quota failure.
- Nine Python tests cover required CI checks, failure/pending/skipped states, reruns, independent check providers, token paths, path containment, API origin restrictions and tier estimates.
- JavaScript files pass `node --check`.
- Python CLI published its own PR, waited for GitHub CI and merged the exact checked commit.

## Browser observations

- All six cards render; counts update target thresholds.
- Manual confirmations update the summary independently of counts.
- Counts and confirmations survive reload.
- Malformed JSON is rejected with a visible Russian error and unchanged records.
- Narrow viewport measured 375 CSS px content width and 375 CSS px viewport width: no horizontal overflow.
- Checkbox accessible names identify their achievement. Import dialog has a label and cancellation is the initial focus target.
- The optional WebMCP read/update tools registered. A valid update was read back; a negative count was rejected.
- Export displayed its completion message. The embedded browser did not expose a download event, so saving the downloaded file was not verified through that browser. Serialization round trips are covered by automated tests.

The screenshot in this directory illustrates manual journal state; it is not a live GitHub status report. Full screen-reader and cross-browser coverage has not been performed.
