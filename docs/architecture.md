# Explore Studio — Architecture

## Overview

*This document defines the high-level technical architecture of Explore Studio.
It is intentionally lightweight during Phase 0 and will be expanded as design
decisions are made.*

## Design Goals

- **Modularity.** Engine, world, lessons, and teacher tools are separate
  packages with clear boundaries.
- **Python-first.** The core engine and lesson framework are implemented
  in Python.
- **Testable.** Every subsystem is designed for isolated unit and
  integration testing.
- **Extensible.** Community contributors can add new lesson modules,
  world entities, and teacher tools without modifying the core.

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
└─────────────────────────────────────────────┘
```

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

*Decisions will be recorded here with rationale as they are made.*
