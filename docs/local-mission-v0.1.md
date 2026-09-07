# Local Mission v0.1

> **Status:** Implemented local, session-only Classroom Trail mission contract.

Local Mission v0.1 provides the reusable immutable mission model used by
Classroom Trail v0.10. Canonical course content owns an immutable ID-keyed
catalog containing thirteen entries:

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

Mission 08:

- mission ID: `respond-to-object-state`;
- title: `Make an If/Else Character`;
- instructions require one NPC linked to a same-package toggle object, one OFF
  response, one ON response, and displaying both branches.

Mission 09:

- mission ID: `count-object-interactions`;
- title: `Power It Up`;
- instructions require a goal from 2 through 5, an authored goal-reached
  message, and reaching every counter object's goal.

Mission 10:

- mission ID: `require-all-switches-on`;
- title: `Unlock the Secret`;
- instructions require one NPC linked to exactly two toggle objects, authored
  fallback and success responses, and displaying both branches.

Mission 11:

- mission ID: `open-with-either-switch`;
- title: `Either Switch Opens It`;
- instructions require one NPC linked to exactly two toggle objects, authored
  locked and open responses, and displaying both-off, first-only, and
  second-only cases.

Mission 12:

- mission ID: `invert-a-switch-condition`;
- title: `Turn the Rule Around`;
- instructions teach the idea of `not` with an NPC whose special response is
  shown while one linked switch is OFF, then require both switch states.

Mission 13:

- mission ID: `compare-a-counter-to-its-goal`;
- title: `Check the Power Level`;
- instructions require one NPC linked to a same-package counter object,
  authored responses for below the goal and at or above the goal, and display
  of both comparison branches.

Each definition contains nonblank `mission_id`, `title`, and `instructions`
fields. Missions 01–03 and 06 use `ALL_OBJECTS_VISITED`; Mission 04 uses
`ALL_INTERACTABLE_NPCS_SPOKEN_TO`; Mission 05 uses
`ALL_CONVERSATION_NPCS_COMPLETED`; Mission 07 uses
`ALL_TOGGLE_OBJECTS_CHANGED`; Mission 08 uses
`ALL_CONDITIONAL_BRANCHES_DISPLAYED`; Mission 09 uses
`ALL_COUNTER_GOALS_REACHED`; Mission 10 uses
`ALL_TWO_TOGGLE_BRANCHES_DISPLAYED`; Mission 11 uses
`ALL_EITHER_TOGGLE_CASES_DISPLAYED`; Mission 12 reuses
`ALL_CONDITIONAL_BRANCHES_DISPLAYED`; Mission 13 uses
`ALL_COUNTER_COMPARISON_BRANCHES_DISPLAYED`. Other rule values are rejected.

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

`ALL_CONDITIONAL_BRANCHES_DISPLAYED` uses a separate, session-only immutable
set of `(npc_qualified_id, is_on)` pairs. A pair is added only when that
authored branch is displayed and is never removed. Both branches are required
for every conditional NPC. Ordinary greeting/conversation NPCs are excluded,
and a Trail with no conditional NPCs does not complete this rule.

`ALL_COUNTER_GOALS_REACHED` uses a separate, session-only immutable mapping of
counter-object qualified IDs to interaction counts. Every counter starts at
zero and increments once per successful targeted interaction. Completion
requires every count to meet or exceed its goal. Ordinary objects are
excluded, and a Trail with no counter objects does not complete this rule.

`ALL_TWO_TOGGLE_BRANCHES_DISPLAYED` uses a separate, session-only immutable set
of `(npc_qualified_id, all_on)` pairs. Fallback evidence is recorded when one
or both referenced toggles are off; success evidence is recorded only when both
are on. Both are required for every two-toggle NPC. Ordinary characters are
excluded, and a Trail with no two-toggle NPC remains incomplete.

`ALL_EITHER_TOGGLE_CASES_DISPLAYED` uses a separate, session-only immutable set
of `(npc_qualified_id, first_on, second_on)` cases. Completion requires both
off, first only, and second only for every either-toggle NPC. Both on selects
the open response and may be retained as evidence but is not required. Zero
either-toggle NPCs remains incomplete.

Mission 12 reuses the existing one-toggle conditional evidence and completion
rule from Mission 08. It introduces no new negation syntax, metadata, runtime
state, or completion rule.

`ALL_COUNTER_COMPARISON_BRANCHES_DISPLAYED` uses a separate, session-only
immutable set of `(npc_qualified_id, at_or_above_goal)` pairs. Interaction with
a qualifying NPC evaluates exactly `count >= goal`, using the current session
count and the referenced counter object's authored goal. Both False and True
must be displayed for every qualifying NPC; zero qualifying NPCs remains
incomplete. Repeated displays are idempotent, evidence is monotonic, and the
comparison does not mutate counters or existing runtime evidence.

The Trail UI displays the mission title, instructions, and either `Incomplete`
or `Complete`. NPC responses provide Missions 04–05 evidence without changing
object state. Object interaction, visited-object progress, Trail completion,
NPC targeting, conversation advancement and wrap, and multi-object package
behavior remain unchanged.

## Deferred

Mission 14+, additional completion rules, mission sequencing, decrement/reset,
arithmetic expressions, general `not` syntax, nested or arbitrary conditions,
choices, memory, quests, generic actions or state machines, rewards,
persistence, teacher controls, deployment, authentication, and Phase E
integration remain out of scope.
