# S29 Evidence-Linked Review Checklist

Use this compact checklist beside the persistent project record.

## Before editing

- [ ] I annotated my own diff/code before outside review.
- [ ] I cited one duplication and one confusing responsibility/name.
- [ ] For each refactor, I predicted risk, catching evidence, and unchanged output.
- [ ] I captured the package file/size/SHA-256 snapshot.

## Review response

- [ ] Every observation cites a location, test, duplication, name, responsibility,
      or observable behavior risk.
- [ ] Every response is accept, reject, or ask one clarification.
- [ ] Accepted items name the change, preserved behavior, and regression evidence.
- [ ] Rejected items give a technical reason.

## Regression and visitor smoke

- [ ] Targeted regression tests pass before and after.
- [ ] Deterministic package snapshot comparison has no unexplained differences.
- [ ] Package validates and plans.
- [ ] Source → Python pipeline → generated YAML → validator → Trail is explained.
- [ ] M14: Echo Lens and Wind Dial share `observatory-glow`.
- [ ] M15: Echo Lens → Wind Dial → Comet Bell completes in order.
- [ ] Existing M15 wrong-member/reset behavior is observed or teacher-demonstrated.
- [ ] Approach, interaction, and clean exit are checked.

## Close

- [ ] Project record contains review decisions, evidence, smoke result, and lesson.
- [ ] Follow-up commits preserve the original reviewed state; no squash is needed.
