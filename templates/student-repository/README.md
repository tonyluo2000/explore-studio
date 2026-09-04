# Explorer Student Repository

This repository owns your project history and one declarative Explorer Package.
The Explore Studio platform remains an installed dependency; engine and platform
code do not belong in this repository.

## Set up and check locally

Create a virtual environment, install the pinned project and test dependencies,
then run:

```bash
explore-package validate explorer-package
pytest
```

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
versioned candidate.

## Future publish workflow

Publishing will be a separate, explicit operation supplied by a future trusted
service. Export does not upload, register, sign, approve, or deploy the package.
Until that service exists, share neither credentials nor claims that an exported
candidate has been published or approved.
