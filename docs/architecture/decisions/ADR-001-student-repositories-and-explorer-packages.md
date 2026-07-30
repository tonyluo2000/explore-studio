# ADR-001: Student Repositories and Explorer Packages

- **Status:** Accepted
- **Date:** 2026-07-29
- **Decision owners:** Explore Studio maintainers and course team

## Context

Explore Studio needs to support a 30-mission course in which students own their
work while contributing to a stable shared class world. Earlier documentation
described student directories and pull requests in one shared repository. That
model makes ownership, permissions, integration, and reproducible releases
harder as the class grows.

Git commits, publishable contributions, and released class worlds have different
trust and lifecycle requirements. Local experimentation also has different
identity requirements from shared online services. Educational progression must
guide students without being mistaken for a source-code or authorization
boundary.

The detailed design is the
[Student Contribution and Class-World Model](../student-contribution-model.md).

## Decision

- Each student works in an independent repository created from a supported
  template.
- Students commit freely to their own repositories.
- Students do not commit directly to the official Explore Studio engine
  repository.
- Shared-world contributions are published as versioned Explorer Packages.
- A class-world release is assembled from approved package versions, an engine
  version, and class configuration.
- Student repositories are not merged together to create the final release.
- Local mode does not require login.
- Online mode requires authenticated identity and server-side authorization.
- Capability progression is controlled for learning purposes, not as a
  source-code security boundary.

The decision defines logical boundaries. The template and builder may begin
inside `explore-studio` and be extracted later without changing the model.
Generated class-world output is a release artifact, not the canonical source of
student work.

> **Everything is already built. Students gradually learn how to use it.**

> **Every Explorer publishes a package. The class world is built from everyone’s contributions.**

> **The platform is shared. The adventure is yours.**

## Consequences

### Positive

- Students have independent ownership and clear commit histories.
- Source-level merge conflicts between students are greatly reduced.
- Students cannot accidentally commit changes to the official engine through
  their normal project workflow.
- The engine and core world remain stable.
- Package validation can run before shared-world assembly.
- Pinned inputs support repeatable class-world releases.
- Contributions can remain usable across cohorts when compatibility permits.
- The workflow teaches realistic distinctions between committing, publishing,
  reviewing, and releasing.

### Costs and risks

- The Explorer Package contract must be designed, versioned, documented, and
  maintained.
- Student templates and engine or Student API compatibility must be managed.
- Package export, validation, registry, and class-world build tooling are
  required.
- Teacher review and approval add operational work.
- Arbitrary student code creates substantial shared-runtime security risks.
- Repository provisioning, access, identity, and recovery require operational
  processes.
- Reproducibility requires pinned dependencies, deterministic tooling, and
  retained artifacts or provenance.

## Alternatives Considered

1. **One shared repository with a directory per student.** Simple initially,
   but ownership, permissions, history, and merge conflicts become shared
   concerns.
2. **Fork the full engine for every student.** Isolates work but duplicates the
   platform and makes upgrades and compatibility difficult.
3. **Manually merge independent student repositories.** Preserves separate
   histories but defers integration risk and does not create a stable
   contribution contract.
4. **One student repository each plus Explorer Packages.** Selected because it
   preserves ownership while providing a versioned, validatable assembly
   boundary.

## Follow-Up Work

1. Prototype the manifest, namespace rules, validator, and two example packages.
2. Implement a local package loader through stable Student API contracts.
3. Build a deterministic class-world assembler and reproducibility tests.
4. Formalize the student repository template and export workflow.
5. Design online authentication, registry, approval, and revocation.
6. Implement mission-based educational presentation independently of
   authorization.
7. Complete a dedicated security design before accepting executable student code
   into shared deployments.

This ADR does not approve a manifest schema, authentication provider, hosting
platform, repository visibility policy, or Python sandbox.
