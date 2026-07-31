# Package-Set Preflight and Selection Model v0.1

> **Status:** Implemented pure multi-package planning layer. Package-set
> application, class-world assembly, release artifacts, publication, and
> approval remain deferred.

Package-Set Preflight v0.1 determines whether an ordered set of exact Explorer
Package versions and their completed Student API registration plans can coexist:

```text
pinned package selections
        +
immutable StudentAPIRegistrationPlan values
        ↓
selection and plan consistency
        ↓
cross-package identity and cardinality checks
        ↓
immutable PackageSetPlan
```

This is a planning boundary. It does not apply a registration plan, select a
target, mutate a `World`, or create a class-world release.

The downstream
[Transactional Package-Set Application v0.1](transactional-package-set-application-v0.1.md)
applies one successful immutable `PackageSetPlan` to one explicit compatible
target with staging and cross-package rollback. Planning itself remains pure.

## Input boundary

Each `PackageSelection` explicitly contains:

- one package ID;
- one exact Semantic Version; and
- one existing immutable `StudentAPIRegistrationPlan`.

```python
from explore.packages import PackageSelection

selection = PackageSelection(
    package_id="nova-character",
    package_version="1.0.0",
    registration_plan=nova_plan,
)
```

Validation, declarative loading, and single-package registration planning must
already have completed. The package-set planner accepts in-memory values only.
It does not accept package directories, `PackageLoadResult` values, version
ranges, release manifests, registry identifiers, or a request for the latest
package version.

## Exact package-version pinning

The selection's package ID and version must exactly equal the corresponding
fields in its registration-plan provenance. Values are not normalized,
inferred, upgraded, or replaced from provenance.

Package IDs use the existing lower-kebab-case Explorer Package identifier
policy. Package versions use exact Semantic Versioning 2.0.0 values. v0.1 does
not resolve version ranges or dependencies.

Within one package set, a package ID may appear only once. Selecting the same
ID twice is an error whether the two selections pin the same version or
different versions. There is no last-selection-wins or override behavior.

## Public API

```python
from explore.packages import build_package_set_plan

result = build_package_set_plan((nova_selection, lantern_selection))
if result.is_planned:
    assert result.plan is not None
    for package in result.plan.packages:
        print(package.package_id, package.package_version)
    for entry in result.plan.entries:
        print(entry.qualified_id)
else:
    for issue in result.issues:
        print(f"{issue.code}: {issue.location}: {issue.message}")
```

The intentional public surface is:

- `build_package_set_plan`;
- `PackageSelection`;
- `SelectedPackagePlan`;
- `PackageSetPlan`;
- `PackageSetPlanResult`;
- `PackageSetIssue`; and
- `PackageSetIssueCode`.

All models are frozen dataclasses. Public package, entry, and issue collections
are tuples. The package-set plan retains each selected package's exact pin,
provenance, and original immutable registration plan. Flattened entries retain
their existing immutable registration values and package provenance.

## Deterministic ordering

Package order is the caller-provided selection order. The planner does not sort
package IDs lexically.

Entry order is flattened by:

1. caller-provided package-selection order; then
2. existing registration-entry order within each selected package plan.

Given identical ordered immutable inputs, successful plans and failure results
are equality-comparable and identical. A later release builder may impose a
different canonical release order, but that is outside this layer.

## Selection and plan consistency

For each selection, preflight checks:

- package ID syntax;
- exact package-version syntax;
- registration-plan type and non-empty tuple structure;
- exact selection-to-provenance package ID and version agreement;
- supported Student API version;
- entry provenance agreement with the containing plan;
- local contribution ID and `package-id:contribution-id` qualified identity;
- supported character or world-object registration type;
- constructor-compatible detached registration values; and
- package-relative PNG metadata for optional image references.

These defensive checks reject inconsistent manually constructed plans. They do
not rerun package validation, loading, or registration planning.

## Student API compatibility

Every selected plan must target the same supported Student API version. v0.1
supports exactly:

```text
0.1
```

Unsupported versions are rejected. Mixed versions receive a deterministic
cross-selection mismatch diagnostic. The planner does not migrate or adapt
plans and does not interpret compatibility ranges.

## Contribution identities

Every registration entry retains both:

- a package-local contribution ID; and
- a qualified `package-id:contribution-id` identity.

Two different packages may use the same local ID:

```text
nova-character:hero
forest-guide:hero
```

Those identities do not collide. Local IDs are namespaced by package ID.

Qualified identities must remain unique across the complete planning attempt.
Preflight checks duplicates both within a manually constructed single-package
plan and across selected package plans. Collision state exists only inside the
current call; no global identity registry is created.

## Aggregate Student API v0.1 cardinality

The currently implemented Student API v0.1 target supports at most:

- one character; and
- one world object.

Package-set preflight therefore applies the same limits across all selected
plans together. It rejects two character registrations or two world-object
registrations whether the conflict occurs within one manual plan or across two
packages.

Every conflicting entry receives a diagnostic in flattened entry order. The
planner does not choose a winner, discard an entry, replace another package, or
invent multiple-entity runtime support. This is a Student API v0.1 limitation,
not a permanent class-world design rule.

## Atomic planning

Planning is all-or-nothing. If any issue exists:

- `PackageSetPlanResult.plan` is `None`;
- no partial `SelectedPackagePlan` collection is exposed;
- no partial flattened entry collection is exposed;
- invalid or conflicting packages are not silently omitted; and
- valid earlier selections do not become an incomplete success.

Independent issues may be accumulated so one run can report useful corrections
without changing the input.

## Diagnostics

`PackageSetIssue` contains a stable code, message, structural location, and
optional package ID, package index, qualified ID, and entry index.

Issue ordering is deterministic:

1. input-level issues;
2. selection-local checks in caller order, with package ID and version before
   plan provenance and entries;
3. duplicate-package and mixed-Student-API checks in caller order;
4. duplicate qualified identities in flattened entry order; and
5. aggregate cardinality issues in flattened entry order.

Messages contain structural locations such as
`selections[1].registration_plan.entries[0]`. They do not contain raw exception
representations, memory addresses, source-machine paths, or repository URLs.

## Safety and non-mutation boundary

Package-set preflight performs no:

- filesystem reads or directory inspection;
- YAML parsing;
- package validation or declarative loading;
- single-package registration planning;
- transactional registration application;
- target lookup or `World` mutation;
- Student API `Character` or `Object` construction;
- asset opening, decoding, or materialization;
- Python module loading from a package;
- student-code evaluation or execution;
- Pygame, renderer, scene, lifecycle, or event-loop initialization;
- network access or version lookup;
- global registry mutation;
- package publication, approval, authentication, or authorization; or
- class-world artifact or release-manifest generation.

The trusted caller supplies selections and already completed plans. Approval and
ownership policy remain separate concerns.

## Implementation status

- single-package validation: implemented;
- single-package declarative loading: implemented;
- single-package registration planning: implemented;
- single-plan transactional application: implemented;
- multi-package package-set preflight: implemented;
- transactional package-set application: implemented;
- class-world assembly: not implemented;
- release artifacts and release manifests: not implemented;
- publication and approval: not implemented.

## Deferred work

- class-world target selection and target-state orchestration;
- class-world configuration and assembly;
- release-manifest schemas;
- cross-package policy beyond current identity and cardinality rules;
- approval, publication, authentication, and registry services;
- artifact reproducibility, content hashes, and retained provenance;
- persistent audit and recovery records;
- archive loading and dependency resolution;
- asset materialization; and
- executable extension support and its required isolation design.
