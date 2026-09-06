# Local Mission v0.1

> **Status:** Implemented local, session-only Classroom Trail mission contract.

Local Mission v0.1 provides the reusable immutable mission model used by
Classroom Trail v0.4. Canonical course content owns an immutable ID-keyed
catalog containing four entries:

- mission ID: `visit-all-classroom-objects`;
- title: `Explore Every Object`;
- instructions: `Interact with every classroom object.`

Mission 02:

- mission ID: `create-a-classroom-object`;
- title: `Create Your First Object`;
- instructions teach students to create a named, positioned, colored world
  object and then interact with every classroom object.

Mission 03:

- mission ID: `make-your-object-respond`;
- title: `Make It Respond`;
- instructions require students to author `when_near` and `when_interacted`
  text for their world object and then interact with every classroom object.

Mission 04:

- mission ID: `introduce-your-character`;
- title: `Give Your Character a Voice`;
- instructions require students to author one character greeting and speak to
  every interactable NPC.

Each definition contains nonblank `mission_id`, `title`, and `instructions`
fields. Missions 01–03 use `ALL_OBJECTS_VISITED`; Mission 04 uses
`ALL_INTERACTABLE_NPCS_SPOKEN_TO`. Other rule values are rejected.

Catalog keys are emitted in deterministic mission-ID order. Exact lookup
returns each canonical immutable definition; unknown or malformed IDs
raise an error and never select a fallback mission. Classroom Trail defaults to
Mission 01 and supports explicit exact-ID local selection. The engine owns the
model and evaluation mechanics, but no authored mission title or instructions.

## Derived completion

Mission completion is derived from the selected fixed rule. Existing
`ClassroomTrailScene.is_complete` and visited-object state remain the source for
`ALL_OBJECTS_VISITED`. `ALL_INTERACTABLE_NPCS_SPOKEN_TO` uses a separate,
session-only immutable set of package-qualified NPC IDs. A successful greeting
display or first conversation response marks that NPC spoken; repeated
interactions are idempotent. Silent NPCs are excluded, and a Trail with no
interactable NPCs does not complete this rule.

The Trail UI displays the mission title, instructions, and either `Incomplete`
or `Complete`. NPC responses provide Mission 04 evidence without changing
object state. Object interaction, visited-object progress, Trail completion,
NPC targeting, and conversation advancement and wrap remain unchanged.

## Deferred

Additional completion rules, full-conversation objectives, mission sequencing,
branching, choices, memory, quests, rewards, persistence, teacher controls,
deployment, authentication, and Phase E integration remain out of scope.
