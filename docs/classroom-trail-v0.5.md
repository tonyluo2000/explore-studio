# Local Classroom Trail v0.5

> **Status:** Implemented additive local runtime contract. Student API and
> package-set v0.1 cardinality remain unchanged.

Classroom Trail v0.5 adds one strict, declarative two-state presentation for
world objects. Existing v0.1 packages without toggle metadata retain their
v0.4 appearance, interaction, targeting, ordering, and visit behavior.

## Toggle declaration

A world object becomes a toggle object only when it declares `toggle`:

```yaml
name: "Magic Switch"
x: 120
y: 460
when_near: "The switch is quiet."
when_interacted: "Click!"
toggle:
  off_color: "red"
  on_color: "green"
```

`toggle` is a mapping containing exactly `off_color` and `on_color`. Both are
required supported Student API v0.1 color names and must be distinct. Unknown
toggle keys fail closed. Top-level `color` and `asset_id` cannot coexist with
`toggle`, preventing competing appearance sources in this bounded slice.
Name, coordinates, `when_near`, and `when_interacted` retain their existing
meaning. An object without `toggle` remains an ordinary object.

The loader derives the object's immutable base color from `off_color` and
retains both authored colors as typed inert metadata. Registration and Trail
planning carry that metadata without executing package code.

## Session state and rendering

Every toggle starts off. The running scene owns two separate immutable sets:

- current-on qualified IDs, which add or remove one targeted toggle per
  successful interaction; and
- changed qualified IDs, which record the first successful toggle interaction
  monotonically.

Rendering projects `off_color` or `on_color` from current session state. It
does not mutate the immutable engine world object. A successful toggle
interaction still records the ordinary visited-object ID. Target selection,
qualified-ID ordering, proximity, prompts, feedback, visited progress, and
`ClassroomTrailScene.is_complete` are unchanged.

## Mission completion

`ALL_TOGGLE_OBJECTS_CHANGED` completes only when every toggle object's
qualified ID is present in changed evidence. Ordinary objects are excluded. A
Trail with no toggle objects remains incomplete. Returning a toggle to off does
not remove its changed evidence. The rule is independent from ordinary
all-object visit completion.

## Compatibility and deferred work

Explorer Package schema and exact Student API compatibility remain `0.1`.
Toggle is optional Trail-only contribution metadata; older loaders reject it
as unknown rather than silently treating it as an ordinary object. The
canonical Trail planner emits contract version `0.5`, and exact version checks
remain fail closed.

State-specific dialogue, conditions, counters, generic state or action
systems, scripting, sequencing, persistence, rewards, teacher controls,
deployment, authentication, and Phase E integration remain deferred.
