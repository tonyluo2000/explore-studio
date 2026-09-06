# Explore Studio

An open-source, interactive educational environment for teaching programming through
game design and world-building.

---

## Vision

Explore Studio turns learning to code into an adventure. Students build and explore
virtual worlds while mastering programming fundamentals, computational thinking, and
creative problem-solving — one interactive lesson at a time.

## Educational Goals

- Teach programming fundamentals through hands-on world-building.
- Develop computational thinking and debugging skills.
- Encourage creative expression alongside technical rigor.
- Support self-paced learning with guided, incremental challenges.
- Provide teachers with tools to design, assign, and assess custom curricula.

## Intended Audience

- **Students** (ages 10+) learning to program for the first time.
- **Teachers** and educators designing programming curricula.
- **Self-learners** looking for an engaging, project-based introduction to coding.
- **Open-source contributors** interested in educational technology.

## Long-Term Roadmap

| Phase | Focus |
|-------|-------|
| 0 | Repository foundation and tooling |
| 1 | Core engine: rendering, input, world model |
| 2 | Lesson framework and first curriculum module |
| 3 | Teacher dashboard and student progress tracking |
| 4 | Community lesson marketplace |

See [`docs/roadmap.md`](docs/roadmap.md) for detail.

## Architecture and Documentation

- [`docs/architecture.md`](docs/architecture.md) — architecture index.
- [`docs/architecture/student-contribution-model.md`](docs/architecture/student-contribution-model.md)
  — student repositories, Explorer Packages, execution modes, progression, and
  class-world assembly.
- [`docs/architecture/decisions/`](docs/architecture/decisions/) — accepted
  architecture decision records.
- [`docs/student-api-v0.1-spec.md`](docs/student-api-v0.1-spec.md) — current
  implemented Student API contract.
- [`docs/classroom-trail-v0.4.md`](docs/classroom-trail-v0.4.md) — additive local
  multi-package Classroom Trail contract.
- [`docs/local-mission-v0.1.md`](docs/local-mission-v0.1.md) — first session-only
  Classroom Trail mission contract.

## Repository Organization

```
explore-studio/
├── docs/           # Project documentation
├── engine/         # Core game engine (rendering, physics, input)
├── explore/        # Student API
├── lessons/        # Lesson definitions and curriculum content
├── tests/          # Test suite
└── pyproject.toml  # Package and tool configuration
```

This repository is the official platform repository. The target course model
uses one independent repository per student; students export versioned Explorer
Package candidates that future trusted workflows can publish for class-world
assembly. Student repositories are created from the standalone
[`student-adventure-template`](https://github.com/tonyluo2000/student-adventure-template),
are not directories in this repository, and are not merged to produce a release.
See the [student contribution model](docs/architecture/student-contribution-model.md).

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE) for details.
