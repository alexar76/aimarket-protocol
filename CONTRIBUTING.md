<!-- satellite-contributing -->

# Contributing to AIMarket Protocol

Pull requests are welcome. History on this repository is append-only, the same as [metis](https://github.com/alexar76/metis) and the factory repo [alexar76/aicom](https://github.com/alexar76/aicom): no force-push. A merged pull request is imported back into the monorepo with `scripts/import_satellite_pr.sh` and re-synced here, so the contribution becomes canonical.

1. Open an issue describing the problem before a normative change. [GOVERNANCE.md](GOVERNANCE.md) is the process: 14 days of comment on a MUST or a wire change, and no such change merges until an implementation has run it.
2. Fork [alexar76/aimarket-protocol](https://github.com/alexar76/aimarket-protocol) and branch from `main`.
3. A change to signed bytes needs a vector in `test-vectors/` in the same change.
4. Patches for the reference hub belong in that hub's repository, not here.

## Pull request checklist

- [ ] **Why** — the problem, then the text.
- [ ] **Vectors** — updated when the signed bytes change.
- [ ] **Secrets** — none in the diff.
