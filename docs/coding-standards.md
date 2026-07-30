# Explore Studio — Coding Standards

## Python Style

- **Formatter:** Black (line length 100).
- **Linter:** Ruff with pycodestyle, pyflakes, isort, pep8-naming,
  pyupgrade, flake8-bugbear, flake8-comprehensions, flake8-simplify.
- **Type hints:** Required for all public APIs. Encouraged internally.
- **Docstrings:** Google-style for public functions and classes.

## Testing

- **Framework:** pytest.
- **Coverage target:** ≥80% for engine code (to be enforced in CI).
- **Test organization:** Mirror the source tree under `tests/`.
- **Naming:** `test_<module>.py` for unit tests,
  `test_<feature>_integration.py` for integration tests.

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): short description

Optional longer description.
```

Types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `style`, `ci`.

## Branch Strategy

- `main` — stable, releasable.
- Feature branches from `main`.
- Pull requests required for all changes.
- Squash merge preferred.

## Documentation

- `docs/architecture.md` is the architecture index.
- Accepted cross-cutting decisions are recorded as numbered ADRs under
  `docs/architecture/decisions/`.
- Detailed architecture belongs in a canonical design document and is linked
  from related specifications rather than copied.
- Public API documented with docstrings.
- Curriculum content documented in `docs/curriculum.md`.

---

*Standards will be refined as the project grows.*
