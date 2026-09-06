# Explore Studio — Architecture

## Overview

*This document defines the high-level technical architecture of Explore Studio.
It is intentionally lightweight and links to the detailed specifications and
decision records that govern each boundary.*

The canonical contribution architecture is
[Student Contribution and Class-World Model](architecture/student-contribution-model.md).
The accepted decision is recorded in
[ADR-001: Student repositories and Explorer Packages](architecture/decisions/ADR-001-student-repositories-and-explorer-packages.md).

## Design Goals

- **Modularity.** Engine, world, lessons, and teacher tools are separate
  packages with clear boundaries.
- **Python-first.** The core engine and lesson framework are implemented
  in Python.
- **Testable.** Every subsystem is designed for isolated unit and
  integration testing.
- **Extensible.** Community contributors can add new lesson modules,
  world entities, and teacher tools without modifying the core.
- **Student-owned.** Each student works in an independent repository and
  publishes versioned Explorer Packages rather than modifying the official
  engine repository.
- **Reproducible.** A class world is generated from pinned engine, package, and
  class-configuration inputs.

## High-Level Components

```
┌─────────────────────────────────────────────┐
│                  Students                    │
│   (entry points, CLI, lesson runner)         │
├─────────────────────────────────────────────┤
│                  Lessons                     │
│   (curriculum, challenges, progression)       │
├─────────────────────────────────────────────┤
│                   World                      │
│   (entities, state, simulation, events)      │
├─────────────────────────────────────────────┤
│                   Engine                     │
│   (rendering, input, physics, audio)         │
├─────────────────────────────────────────────┤
│                  Teacher                     │
│   (dashboard, authoring, assessment)         │
├─────────────────────────────────────────────┤
│            Contribution Pipeline              │
│   (packages, validation, class-world build)   │
└─────────────────────────────────────────────┘
```

Local projects run without login. Online services use authenticated identity and
server-side authorization. The engine should reach these modes through stable
provider boundaries rather than treating a local directory as online identity.

## Architecture Documents

- [Engine Architecture Specification](engine-architecture.md)
- [Repository Architecture Specification](repository-architecture.md)
- [Student API Specification](student-api-spec.md)
- [Student API v0.1 Specification](student-api-v0.1-spec.md)
- [Local Classroom Trail v0.4](classroom-trail-v0.4.md)
- [Explorer World Design Specification](explorer-world-spec.md)
- [Student Contribution and Class-World Model](architecture/student-contribution-model.md)
- [Phase E Online Foundation v0.1](phase-e-foundation-v0.1.md)
- [Phase E Package Submission v0.1](phase-e-submission-v0.1.md)
- [Phase E Package Review Decisions v0.1](phase-e-review-v0.1.md)
- [Phase E Approved Registry Projection v0.1](phase-e-registry-v0.1.md)
- [Phase E Exact Approved-Version Pinning v0.1](phase-e-pinning-v0.1.md)
- [Phase E Authenticated Control Plane v0.1](phase-e-control-plane-v0.1.md)
- [Phase E Authoritative Class-World Configuration Store v0.1](phase-e-configuration-store-v0.1.md)
- [Phase E Staff Transport Foundation v0.1](phase-e-staff-transport-v0.1.md)
- [Phase E Synthetic Staff Pilot Hardening v0.1](phase-e-staff-pilot-v0.1.md)
- [Architecture Decision Records](architecture/decisions/)

## Technology Stack (Planned)

| Layer | Candidates |
|-------|-----------|
| Language | Python 3.11+ |
| Rendering | Pygame (initial), potentially Panda3D or Pyglet later |
| Testing | pytest |
| Linting / Formatting | Ruff, Black |
| Packaging | setuptools / pyproject.toml |

## Decisions Pending

- Rendering backend selection.
- World entity model (ECS vs inheritance).
- Lesson serialization format.
- Teacher dashboard technology (web vs desktop).
- Student progress persistence.

---

*Accepted cross-cutting decisions are recorded under
[`docs/architecture/decisions/`](architecture/decisions/).*
