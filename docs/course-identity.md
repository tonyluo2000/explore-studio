# Course Identity

> **Status:** Canonical course-wide design principles. S01–S02 implement them
> first; later sessions adopt them incrementally.

**Explore Studio: learn Python by building an explorer, programming a
companion, and using them to investigate interesting worlds and real ideas.**

Python is the academic subject. Explorers, companions, illustrated worlds, and
real-world discoveries are the motivation and the application layer.

## A. Python first

Every session answers three questions, in this order of priority:

1. **What did I learn in Python?**
2. **What did my Python allow me to build or do?**
3. **What did I discover about the real world?**

The world must never hide the Python learning objective. Students should
finish the year thinking "I learned Python by building and exploring
interactive worlds", not "I took a game-development class". When a session
runs short, cut world polish before Python instruction.

## B. Explorer + companion

Over the year, every student creates their own **explorer**, their own
**companion**, and their own **world or project**. Creative identity begins in
S01–S02; Python gradually gives those creations capabilities. The recurring
teaching question is:

> What can your companion do now because of the Python you learned?

The intended long-range mapping, introduced only when each concept is taught:

| Python concept | What it gives the explorer or companion |
|---|---|
| variables | identity and state |
| functions | reusable companion actions |
| lists | collections of discoveries |
| loops | examining many discoveries |
| dictionaries | richer character and world data |
| if/else | decisions |
| boolean logic | more complex rules |
| counters | tracking observations and actions |
| testing and debugging | proving behavior works |

S01 and S02 establish the idea only. S02 records one **future ability** as a
plan (a string), not as runtime behavior.

## C. Real-world discovery

Exploration increasingly connects to accurate real-world knowledge:
geography, navigation, history, science, engineering, nature, astronomy,
weather, mathematics, and culture. Discovery material always separates the two
layers:

- **In Nova's world:** fiction, such as the Moon Compass.
- **In our world:** checked facts, such as how a magnetic compass works.

Fictional behavior is never presented as scientific fact. A session gets a
Discovery page only when there is an honest real-world connection; S01 has
none, and that is fine.

## D. Visual north star

The target look is an illustrated exploration world: a polished indie
educational adventure, not debugging circles on an empty screen, and not a
AAA production. Reference visuals, such as slides and course pages, may be
richer than what a beginning student can build. Visual work stays in course
materials unless a runtime change is separately planned.

## Reference cast and categories

Keep these four categories explicit in every lesson that uses them.

| Category | Reference | Notes |
|---|---|---|
| Explorer | **Nova** | Curious, adventurous, wants to understand the world. Player character in `examples/explorer-packages/nova-character`. |
| Companion | **Pixel** | A small, friendly exploration robot: curious but somewhat cautious; helps Nova notice and question discoveries. Static character in `examples/explorer-packages/pixel-companion`. |
| Tool | **Moon Compass** | An exploration instrument. Never a companion. |
| World object | **Crystal Lantern** | Part of the world. Never a companion. |

### Engine honesty

Pixel uses only existing character capabilities: a name, a position, a color,
and a greeting. In the current runtime Pixel **does not** follow Nova,
remember anything between sessions, decide anything, carry items, or keep
hidden state. The story may describe these as future abilities. It must not
imply that the runtime already has them.

## Session page patterns

Each session can carry two short student pages in its `student/` folder. They
reach students through the normal Course Kit provisioning, with no extra
distribution step:

- `python-notes.md`: **What We Learned in Python**, always these seven
  sections: *Python concept*, *Code we wrote*, *What the code means*, *Why
  programmers use this*, *What we debugged*, *Key Python words*, *Try it
  yourself*. Keep it short: a page, not a textbook chapter.
- `discovery.md`: **What We Discovered**, used only where a real connection
  exists, with *In Nova's world* and *In our world* sections.

The website mirrors these pages at `/students/learn/sNN/`, generated from one
typed data file (`course4teen-website/lib/learn.ts`). Add a session there when
its notes are written; never publish empty placeholders.

## Course Kit and Student Workspace

Students never work in the Explore Studio source repository. They receive:

- the **Course Kit** (`explore-studio-course`, the student ZIP): lessons,
  Python Notes, Discovery pages, examples, `START-HERE.md`,
  `check-my-computer.py`, and `make-my-world.py`. It is **replaceable**: a
  teacher may hand out a newer copy at any time;
- the **Student Workspace** (`my-explore-world`, created next to the Course
  Kit by `make-my-world.py`): `explorer.py`, `companion.py`, and `projects/`.
  It **belongs to the student** and must survive every Course Kit update.

The invariant: **course updates never overwrite student work.**
`make-my-world.py` copies only missing template files, never replaces an
existing file, refuses a location inside the Course Kit, and needs no Git,
account, or network. The kit builder refuses any `my-explore-world` member, so
a kit can never absorb or publish a student's workspace. See
[Classroom Student Workspace](classroom-student-workspace.md#course-kit-and-student-workspace).

Lesson files such as `starter.py` and each session's `explorer-package/` stay
in the Course Kit as practice for that day. Moving longer-lived work, such as a
student's own Explorer Package or capstone, into the Student Workspace is later
work; S03 onward are unchanged for now.
