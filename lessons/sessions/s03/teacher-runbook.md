# S03 — Make the World React

**Canonical mission:** M03 `make-your-object-respond` — Make It Respond

**Audience and format:** Ages 10–14, online, 45 minutes

**Learning objective:** Students can use f-strings to compose near and
interaction messages from an object-name variable and predict which event
reveals each message.

**Prerequisite:** S02 variables and strings.

## Before class

- Send `student/task-card.md` and confirm the shared Quick Start preflight.
- Run the starter and validate the package.
- Be ready to demonstrate “move near” separately from “press interact.” Avoid
  introducing general event systems; use the two existing declarative fields.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:05 | 4–5 min | Ask how a silent prop could hint at a secret. | Invents one nearby clue and one discovery. |
| 0:05–0:12 | 6–8 min | Build one f-string together and contrast the two package event fields. | Predicts near vs. interacted behavior. |
| 0:12–0:24 | 11–15 min | Students complete the intentionally minimal near f-string, author the second response, and run locally. | Prints two lines and explains brace substitution. |
| 0:24–0:37 | 9–13 min | Students transfer plain text to YAML, validate, and exercise proximity and interaction separately. | Observes both events and completes M03. |
| 0:37–0:42 | 4–6 min | Lead the task card's edit → predict → run → restore brace exercise and reason about swapped fields. | Restores working code and explains the mapping. |
| 0:42–0:45 | 3–5 min | Compare prediction/result and inspect status/diffs; commit or schedule it. | Descriptive commit or documented plan. |

**Teacher cut line:** At 0:35, stop wording revisions. Protect one completed
f-string explanation and separate evidence for near versus E interaction. Use a
teacher demonstration if bandwidth blocks the Trail; move Git after class.

## Student task and event prediction

Students follow `student/task-card.md`. Its starter deliberately prints only the
object name for `near_message` until the student constructs the clue.

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

Use the task card's explicit edit → predict → run → restore workflow. The
temporary malformed line removes the closing brace:

```python
near_message = f"The {object_name needle begins to shimmer."
```

Then check a possible event mix-up: what behavior would you observe if the two
valid YAML message values were accidentally swapped?

## Expected output and behavior

Before student work, the starter prints `Moon Compass` as its intentionally
unfinished near message, followed by the complete sample interaction message.
After the core task, both printed lines include the object name and authored
story text. In the world, approaching displays the near clue; interacting
displays the discovery. Package validation succeeds and M03 completes after
every world object is interacted with.

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
git diff --staged
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
- If a student cannot restore the line, use the support shape from the task card
  and ask them to identify the substituted variable before typing it.
- Use the shared Quick Start for launch, accessibility, Git, and recovery.
