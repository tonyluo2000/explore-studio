import Link from "next/link";
import { currentJourney, JOURNEY_HREF, journeyContext } from "../../lib/journey";

/**
 * Compact "where we are" panel for a published session's Slides or Notes
 * page. Renders nothing for a session without a published Journey stop.
 */
export default function JourneyContext({ session }: { session: string }) {
  const stop = journeyContext(session);
  if (!stop) return null;
  return (
    <aside className="journey-context" aria-label={`${stop.session.id} in the class Journey`}>
      <dl>
        <div>
          <dt>Where we are</dt>
          <dd>{stop.location}</dd>
        </div>
        <div>
          <dt>Story</dt>
          <dd>{stop.story}</dd>
        </div>
        <div>
          <dt>Journey</dt>
          <dd>
            Session {stop.session.number} of {currentJourney.totalSessions} &middot;{" "}
            <Link className="journey-context-link" href={JOURNEY_HREF}>
              Journey Map <span aria-hidden="true">&rarr;</span>
            </Link>
          </dd>
        </div>
      </dl>
    </aside>
  );
}
