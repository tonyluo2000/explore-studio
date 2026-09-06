# Local Mission v0.1

> **Status:** Implemented local, session-only Classroom Trail mission contract.

Local Mission v0.1 provides the reusable immutable mission model used by
Classroom Trail v0.5. Canonical course content owns an immutable ID-keyed
catalog containing seven entries:

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

Mission 05:

- mission ID: `write-a-short-conversation`;
- title: `Write a Conversation`;
- instructions require students to author one 2–3-line character conversation
  and speak through every conversation NPC's final line.

Mission 06:

- mission ID: `build-an-object-collection`;
- title: `Build a Curious Collection`;
- instructions require three related objects with distinct names, positions,
  colors, and responses, followed by interaction with every classroom object.
- exactly three authored objects is curriculum and static-validation evidence;
  local runtime completion does not enforce that artifact count.

Mission 07:

- mission ID: `toggle-an-object-state`;
- title: `Flip a Magic Switch`;
- instructions require one object with distinct off and on colors, followed by
  at least one interaction with every toggle object.

Each definition contains nonblank `mission_id`, `title`, and `instructions`
fields. Missions 01–03 and 06 use `ALL_OBJECTS_VISITED`; Mission 04 uses
`ALL_INTERACTABLE_NPCS_SPOKEN_TO`; Mission 05 uses
`ALL_CONVERSATION_NPCS_COMPLETED`; Mission 07 uses
`ALL_TOGGLE_OBJECTS_CHANGED`. Other rule values are rejected.

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

`ALL_CONVERSATION_NPCS_COMPLETED` uses a separate, session-only immutable set
of package-qualified NPC IDs. An NPC enters that set when its final authored
conversation line is displayed. Greeting-only and silent NPCs are excluded,
and a Trail with no conversation NPCs does not complete this rule. Repeated
completion and later conversation wrap leave the evidence intact.

`ALL_TOGGLE_OBJECTS_CHANGED` uses a separate, session-only immutable set of
package-qualified toggle-object IDs. An object enters that set on its first
successful toggle interaction and remains there after later toggles. Ordinary
objects are excluded, and a Trail with no toggle objects does not complete
this rule. Current on/off state remains separate from monotonic changed
evidence and ordinary visited-object progress.

The Trail UI displays the mission title, instructions, and either `Incomplete`
or `Complete`. NPC responses provide Missions 04–05 evidence without changing
object state. Object interaction, visited-object progress, Trail completion,
NPC targeting, conversation advancement and wrap, and multi-object package
behavior remain unchanged.

## Deferred

Additional completion rules, mission sequencing, branching, choices,
conditions, memory, quests, rewards, persistence, teacher controls, deployment,
authentication, and Phase E integration remain out of scope.
