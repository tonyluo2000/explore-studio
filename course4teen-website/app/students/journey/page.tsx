import type { Metadata } from "next";
import Link from "next/link";
import SiteHeader from "../../components/SiteHeader";
import SiteFooter from "../../components/SiteFooter";
import JourneyMap, { landmarkNumbers } from "../../components/JourneyMap";
import { classSessions, formatSessionDate } from "../../../lib/calendar";
import { currentJourney, frontierTeaser, JOURNEY_HREF, journeyMapSize } from "../../../lib/journey";

export const metadata: Metadata = {
  title: "Journey Map · The Class Expedition | Course4Teen",
  description:
    "The Course4Teen class Journey: an illustrated map of Nova's world that reveals new ground as each session is taught, with the Trail snapshot, slides, and Python notes for every stop.",
  alternates: { canonical: JOURNEY_HREF },
};

const journey = currentJourney;
const current = journey.currentStop;
const taughtCount = journey.stops.length;
const ahead = classSessions.slice(taughtCount);

export default function JourneyPage() {
  const numbers = landmarkNumbers(journey);
  const frontier = journey.regions.find((region) => region.frontier);
  const fogged = journey.regions.filter((region) => !region.frontier && region.state === "fogged");

  return (
    <>
      <a className="skip-link" href="#main">Skip to content</a>
      <SiteHeader />
      <main id="main">
        <section className="section journey-hero">
          <p className="kicker">Course Journey</p>
          <h1>One expedition, session by session.</h1>
          <p className="calendar-lede">
            Our class&rsquo;s shared map of Nova&rsquo;s world. New ground
            appears as each session is taught, so the map shows where the whole
            class has travelled together, not any one student&rsquo;s progress.
          </p>
          <dl className="journey-now">
            <div className="journey-now-current">
              <dt>Current stop</dt>
              <dd>
                <a href={`#stop-${current.session.id.toLowerCase()}`}>
                  {current.session.id} &middot; {current.place}
                </a>
              </dd>
            </div>
            <div>
              <dt>Class journey</dt>
              <dd>
                {taughtCount} / {journey.totalSessions}{" "}
                <span className="journey-now-note">sessions taught</span>
              </dd>
            </div>
            {journey.nextSession ? (
              <div>
                <dt>Next session</dt>
                <dd>
                  {journey.nextSession.id} &middot; {journey.nextSession.title}{" "}
                  <span className="journey-now-note">{formatSessionDate(journey.nextSession.date)}</span>
                </dd>
              </div>
            ) : null}
          </dl>
        </section>

        <section className="journey-map-section" aria-labelledby="journey-map-heading">
          <div className="journey-map-inner">
            <h2 id="journey-map-heading" className="journey-map-heading">
              The map so far
            </h2>
            <figure className="journey-map-figure">
              <div className="journey-map-frame">
                <JourneyMap state={journey} width={journeyMapSize.width} height={journeyMapSize.height} />
              </div>
              <figcaption className="journey-key">
                <p className="journey-key-title">Map key</p>
                <ol className="journey-key-list">
                  {journey.landmarks.map((landmark) => (
                    <li key={landmark.id} className={landmark.name ? undefined : "journey-key-hinted"}>
                      <span className="journey-key-num" aria-hidden="true">
                        {landmark.name ? numbers.get(landmark.id) : "?"}
                      </span>
                      {landmark.name ? (
                        <span>
                          <strong>{landmark.name}</strong>
                          {landmark.state === "current" ? (
                            <span className="journey-key-current"> &middot; current stop</span>
                          ) : null}
                        </span>
                      ) : (
                        <span>
                          <em>{landmark.hint}</em> &middot; not yet named
                        </span>
                      )}
                    </li>
                  ))}
                  {fogged.map((region) => (
                    <li key={region.id} className="journey-key-hinted">
                      <span className="journey-key-num" aria-hidden="true">~</span>
                      <span><em>Hills under mist</em> &middot; not yet explored</span>
                    </li>
                  ))}
                  {frontier ? (
                    <li className="journey-key-hinted">
                      <span className="journey-key-num" aria-hidden="true">~</span>
                      <span>
                        <em>Uncharted, under mist</em> &middot; {frontierTeaser}
                      </span>
                    </li>
                  ) : null}
                </ol>
                <ul className="journey-key-legend">
                  <li><span className="journey-swatch journey-swatch-trail" aria-hidden="true" /> Painted trail</li>
                  {journey.paths.some((path) => path.kind === "bearing") ? (
                    <li><span className="journey-swatch journey-swatch-bearing" aria-hidden="true" /> Moonlight bearing, no road</li>
                  ) : null}
                  <li><span className="journey-swatch journey-swatch-gem" aria-hidden="true" /> Current stop</li>
                </ul>
              </figcaption>
            </figure>
          </div>
        </section>

        <section className="section journey-stops" aria-labelledby="journey-stops-heading">
          <p className="kicker">Stops so far</p>
          <h2 id="journey-stops-heading">Where the class has been</h2>
          <ol className="journey-stop-list">
            {journey.stops.map((stop) => {
              const isCurrent = stop.session.id === current.session.id;
              return (
                <li
                  key={stop.session.id}
                  id={`stop-${stop.session.id.toLowerCase()}`}
                  className={isCurrent ? "journey-stop journey-stop-current" : "journey-stop"}
                >
                  {/* Plain img: the static export serves the committed 480w and 960w files as-is. */}
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    className="journey-stop-shot"
                    src={stop.hero.small.src}
                    srcSet={`${stop.hero.small.src} ${stop.hero.small.width}w, ${stop.hero.full.src} ${stop.hero.full.width}w`}
                    sizes="(min-width: 900px) 360px, (min-width: 640px) 44vw, calc(100vw - 2rem)"
                    width={stop.hero.small.width}
                    height={stop.hero.small.height}
                    alt={stop.hero.alt}
                    loading="lazy"
                    decoding="async"
                  />
                  <div className="journey-stop-body">
                    <p className="journey-stop-meta">
                      <span className="calendar-session-id">{stop.session.id}</span>
                      <span>{formatSessionDate(stop.session.date)}</span>
                      {isCurrent ? <span className="journey-stop-flag">Current stop</span> : null}
                    </p>
                    <h3>{stop.session.title}</h3>
                    <p className="journey-stop-place">{stop.location}</p>
                    <p className="journey-stop-story">{stop.story}</p>
                    <p className="journey-stop-links">
                      {stop.slidesHref ? <Link href={stop.slidesHref}>Slides</Link> : null}
                      {stop.notesHref ? <Link href={stop.notesHref}>Python notes</Link> : null}
                    </p>
                  </div>
                </li>
              );
            })}
          </ol>

          <h2 className="journey-ahead-heading">Still ahead</h2>
          <p className="calendar-lede">
            Each session&rsquo;s place on the map is revealed when it is taught.
          </p>
          <ol className="calendar-list journey-ahead" start={taughtCount + 1}>
            {ahead.map((session) => (
              <li key={session.id} className="calendar-item">
                <div className="calendar-row">
                  <span className="calendar-session-id">{session.id}</span>
                  <span className="calendar-date">{formatSessionDate(session.date)}</span>
                  <span className="calendar-title slides-pending">
                    {session.title} <em>&mdash; coming soon</em>
                  </span>
                </div>
              </li>
            ))}
          </ol>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
