# S03 — Make the World React

**Canonical mission:** M03 `make-your-object-respond` — Make It Respond

**Audience and format:** Ages 10–14, online, 45 minutes

**Learning objective:** Students can use f-strings to compose near and
interaction messages from an object-name variable and predict which event
reveals each message.

**Prerequisite:** S02 variables and strings.

## Before class

- Run the starter and validate the package.
- Be ready to demonstrate “move near” separately from “press interact.” Avoid
  introducing general event systems; use the two existing declarative fields.

## 45-minute runbook

| Time | Teacher move | Student evidence |
|---:|---|---|
| 0:00–0:05 | Ask how a silent prop could hint at a secret. | Invents one nearby clue and one discovery. |
| 0:05–0:12 | Build one f-string together. Ask which player action should reveal each message. | Predicts near vs. interacted behavior before testing. |
| 0:12–0:24 | Students personalize `object_name` and both composed messages, then run locally. | Prints two complete lines containing the chosen name. |
| 0:24–0:37 | Students transfer their authored text to `when_near` and `when_interacted`, validate, and run M03. | Observes the two events separately and completes the object tour. |
| 0:37–0:42 | Present the malformed f-string below. Students predict, repair, and retest both world events. | Explains braces and event-to-field mapping. |
| 0:42–0:45 | Students state prediction versus result and inspect their diff. | Descriptive commit. |

## Student task and event prediction

Complete this sentence before running the Trail: “Moving near will show ___;
pressing interact will show ___.” Personalize both Python messages and their
matching declarative package fields.

```console
python lessons/sessions/s03/student/starter.py
explore-package validate lessons/sessions/s03/student/explorer-package
explore-package trail \
  examples/explorer-packages/nova-character \
  lessons/sessions/s03/student/explorer-package \
  --player "nova-character:nova" \
  --mission-id "make-your-object-respond" \
  --name "S03 Make the World React"
```

Approach without interacting, record the first message, then interact and
record the second. Complete the mission by interacting with every world object.

## Deliberate debugging exercise

Predict what is malformed here and repair only the missing character:

```python
near_message = f"The {object_name needle begins to shimmer."
```

Then check a possible event mix-up: what behavior would you observe if the two
valid YAML message values were accidentally swapped?

## Expected output and behavior

The starter prints the near message followed by the interaction message, both
including `Moon Compass`. In the world, approaching displays the near clue;
interacting displays the discovery. Package validation succeeds and M03
completes after every world object is interacted with.

## Bounded AI assistance

Student sequence: explain intent → predict → ask one bounded question → test →
revise → explain accepted code. AI may suggest wording revisions only after the
student writes both original lines. It may explain one brace or field mismatch;
it may not author either message or invent a new event.

## Git close

```console
git status --short
git diff
git add lessons/sessions/s03/student
git commit -m "Add moon compass response messages"
```

## Optional extension

Revise the nearby line to foreshadow the interaction line without revealing the
whole surprise. Keep exactly the existing two response fields.

## Teacher notes and answer key

- Correct Python: `near_message = f"The {object_name} needle begins to shimmer."`
- If values are swapped, the discovery appears merely by approaching and the
  clue appears after interaction. Repair the YAML field assignment.
- Reinforce that the f-string exercise helps compose text; the package receives
  plain declarative strings and is validated before use.
