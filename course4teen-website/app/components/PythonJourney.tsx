import Link from "next/link";
import { sessionsWithNotes } from "../../lib/learn";
import {
  publishedPythonSteps,
  pythonJourneyThrough,
  PYTHON_JOURNEY_HREF,
  totalPythonSteps,
} from "../../lib/pythonJourney";

type Props =
  | { mode: "compact"; session: string }
  | { mode: "full"; session?: never };

/** Shared programming companion to JourneyContext's world progression. */
export default function PythonJourney(props: Props) {
  const compact = props.mode === "compact";
  const steps = compact ? pythonJourneyThrough(props.session) : publishedPythonSteps;
  const current = steps.at(-1);
  if (!current) return null;

  return (
    <aside
      className={`python-journey python-journey-${props.mode}`}
      aria-label={compact ? `${current.id} Python Journey` : "Published Python Journey"}
      data-python-current={current.id}
    >
      <p className="python-journey-label">Python Journey</p>
      <h2>{compact ? current.topic : "What we can do with Python"}</h2>
      <p className="python-journey-progress">
        <strong>{steps.length} / {totalPythonSteps}</strong> Python steps
        <span> · {compact ? "Through this session" : "Our class so far"}</span>
      </p>

      {compact ? (
        <>
          <ul className="python-journey-concepts" role="list" aria-label="Key concepts this session">
            {current.concepts.slice(0, 4).map((concept) => <li key={concept}>{concept}</li>)}
          </ul>
          <p className="python-journey-capability"><strong>Now I can…</strong> {current.capability}</p>
          <h3>Python Journey so far</h3>
        </>
      ) : (
        <p className="python-journey-intro">Each session builds on the Python we already know.</p>
      )}

      <ol className="python-journey-steps" role="list" aria-label="Python Journey so far">
        {steps.map((step) => {
          const isCurrent = step.id === current.id;
          return (
            <li key={step.id} data-python-step={step.id} aria-current={isCurrent ? "step" : undefined}>
              <div className="python-journey-step-heading">
                <span className="python-journey-id">{step.id}</span>
                <strong>{step.topic}</strong>
                {isCurrent ? <span className="python-journey-current">You are here</span> : null}
              </div>
              {!compact ? (
                <>
                  <ul className="python-journey-concepts" role="list" aria-label={`${step.id} concepts`}>
                    {step.concepts.map((concept) => <li key={concept}>{concept}</li>)}
                  </ul>
                  <p className="python-journey-capability"><strong>Now I can…</strong> {step.capability}</p>
                  {sessionsWithNotes.includes(step.id) ? (
                    <Link className="python-journey-link" href={`/students/learn/${step.id.toLowerCase()}/`}>{step.id} Python notes</Link>
                  ) : null}
                </>
              ) : null}
            </li>
          );
        })}
      </ol>

      {compact ? (
        <Link className="python-journey-link" href={PYTHON_JOURNEY_HREF}>Full Python Journey <span aria-hidden="true">→</span></Link>
      ) : steps.length < totalPythonSteps ? (
        <p className="python-journey-next">Next: coming soon. New Python steps appear when their slides are published.</p>
      ) : null}
    </aside>
  );
}
