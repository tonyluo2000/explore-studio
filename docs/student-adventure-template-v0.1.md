# Standalone Student Adventure Template v0.1

> **Status:** Extracted Phase D template contract. The standalone repository is
> student-project scaffolding; Explore Studio retains the package contract,
> validator, export tooling, and integration expectations.

The canonical template is the public GitHub template repository
[`tonyluo2000/student-adventure-template`](https://github.com/tonyluo2000/student-adventure-template).
Its extraction head is
`22afcc5c6f4f24ffd7e67d8ff70b0f8d49f5ff38`, created from the nine tracked
template files at Explore Studio
`17f6de56eebeb7354657fcc155f6e2100cc7bff0`. The standalone repository adds only
its own bootstrap, validation, test, and export CI workflow.

## Ownership boundary

Explore Studio maintainers own the template contract and platform tooling. They
maintain the standalone starting scaffold and its compatibility pin. A student
creates a new repository from that template; the new repository owns its Git
history and the student's original project material. The template's licensing
and ownership guidance remains authoritative for scaffold and student work.

No production Explore Studio code reads the standalone repository or depends on
a checkout path. The integration below is maintainer verification only.

## Bootstrap and compatibility pin

The standalone `requirements-dev.txt` retains both the declared
`explore-studio==0.1.0` dependency and the canonical source pin:

```text
explore-studio @ git+https://github.com/tonyluo2000/explore-studio.git@70841376ddd58b82cd606d55d3703e86d8a4dccf
```

Its README documents clean virtual-environment setup, validation, tests, and
deterministic local export. Export retains the documented POSIX descriptor
confinement boundary and fails closed on unsupported native Windows platforms.

## Integration verification

Maintainers can run the pinned network integration explicitly:

```bash
EXPLORE_STUDIO_RUN_TEMPLATE_INTEGRATION=1 \
  pytest tests/test_student_adventure_template_integration.py
```

The integration fetches the exact standalone head, verifies the complete Git
tree and file modes, rejects copied platform source, installs the documented
pin in an isolated environment, and runs validate, pytest, and export without a
monorepo import path. Normal offline test runs skip this network boundary; the
dedicated GitHub Actions workflow enables it.

Future template changes occur in the standalone repository first. After its CI
passes, an Explore Studio integration update may advance the expected template
head and tree in one reviewed change. That maintenance does not alter package or
export semantics.
