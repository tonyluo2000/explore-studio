# Explorer Student Repository

This repository owns your project history and one declarative Explorer Package.
The Explore Studio platform remains an installed dependency; engine and platform
code do not belong in this repository.

## Choose your package identity

Before your first commit, replace `student-beacon` in
`explorer-package/manifest.yaml` with a package ID assigned for your project.
Package IDs use lowercase letters, digits, and hyphens, begin with a letter, and
must remain stable after you begin exporting versions. Update the display name,
contribution ID, and project name in `pyproject.toml` for your adventure too.

## Set up a clean checkout

Explorer Package export v0.1 requires Python 3.11 or newer and a POSIX platform
with descriptor-confined filesystem operations. It is supported on macOS and
Linux environments that provide those operations; native Windows export is not
supported by this contract.

From the repository root, create a virtual environment and install the exact
Explore Studio 0.1.0 source pin plus the student test dependency:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
explore-package validate explorer-package
pytest
```

`requirements-dev.txt` is the canonical bootstrap input. It pins Explore Studio
to an exact commit in the public canonical GitHub repository rather than relying
on an unverified package-index name.

Validation and tests are local checks. They do not execute package code, contact
a service, approve content, or publish anything.

## Commit your source

Edit only your repository's package declarations, assets, tests, and
documentation. Commit when you want to record a meaningful source change:

```bash
git add explorer-package tests README.md
git commit -m "Describe the adventure change"
```

A commit records source history. It is not a package export, approval, or
publication.

## Export a local package candidate

The package ID and version in `explorer-package/manifest.yaml` determine the
required filename. For this starter package, run:

```bash
explore-package export explorer-package \
  --output dist/student-beacon-1.0.0.explorer-package.zip \
  --json
```

Export validates and safely rereads the manifest and declared files, then writes
a deterministic ZIP and reports its raw archive SHA-256. Generated files under
`dist/` are ignored by Git. Change the manifest version before exporting a new
versioned candidate. Export creates a local candidate; it does not submit it.

## Future publish workflow

Publishing will be a separate, explicit submission operation supplied by a
future trusted service. Export does not upload, register, sign, approve, or
deploy the package. Until that service exists, share neither credentials nor
claims that an exported candidate has been published or approved.

## Ownership and licensing

The unchanged template scaffold is provided under the Explore Studio MIT license
in `LICENSES/EXPLORE-STUDIO-MIT.txt`. You retain ownership of original stories,
declarations, tests, artwork, audio, and other work you add. Using this template
does not grant Explore Studio or a course operator permission to publish your
work, and it does not automatically apply the scaffold's MIT license to your new
work. Any future sharing or publication workflow must state its licensing,
attribution, consent, and reuse terms separately before you submit a package.
