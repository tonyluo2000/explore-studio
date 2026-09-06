# Local Mission v0.1

> **Status:** Implemented local, session-only Classroom Trail mission contract.

Local Mission v0.1 adds one immutable mission definition to Classroom Trail
v0.4:

- mission ID: `visit-all-classroom-objects`;
- title: `Explore Every Object`;
- instructions: `Interact with every classroom object.`

The definition contains nonblank `mission_id`, `title`, and `instructions`
fields. Its completion rule is the sole supported rule,
`ALL_OBJECTS_VISITED`. Other rule values are rejected.

## Derived completion

Mission completion is exactly the existing `ClassroomTrailScene.is_complete`
value. The scene does not store, mutate, serialize, or persist a separate
mission-completion flag. Existing visited-object state is additive and
idempotent, so the derived mission status is session-only and monotonic.

The Trail UI displays the mission title, instructions, and either `Incomplete`
or `Complete`. NPC greetings and conversations do not affect mission status.
Object interaction, visited-object progress, Trail completion, NPC targeting,
and conversation advancement remain unchanged.

## Deferred

NPC objectives, additional completion rules, mission sequencing, rewards,
persistence, teacher controls, deployment, authentication, and Phase E
integration remain out of scope.
