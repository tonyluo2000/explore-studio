import type { Metadata } from "next";
import Link from "next/link";
import SiteHeader from "../components/SiteHeader";
import SiteFooter from "../components/SiteFooter";
import {
  breakPeriods,
  classSessions,
  formatBreakRange,
  formatSessionDate,
  sessionsWithSlides,
} from "../../lib/calendar";

export const metadata: Metadata = {
  title: "Class Calendar | Course4Teen",
  description:
    "All 30 Course4Teen session dates for the 2026-27 school year, mapped to the HXGNY school calendar, with break weeks called out.",
  alternates: { canonical: "/calendar/" },
};

const HXGNY_CALENDAR_URL =
  "https://www.hxgny.org/wp/wp-content/uploads/2026/04/2026-27-HXGNY-School-Calendar.pdf";

export default function CalendarPage() {
  const breaksAfter = new Map(breakPeriods.map((b) => [b.afterSessionId, b]));

  return (
    <>
      <a className="skip-link" href="#main">Skip to content</a>
      <SiteHeader />
      <main id="main">
        <section className="section calendar-hero">
          <p className="kicker">2026&ndash;27 school year</p>
          <h1>Thirty Saturdays.<br />One class calendar.</h1>
          <p className="calendar-lede">
            Course4Teen meets live on the Saturday that ends each numbered
            school week on the{" "}
            <a className="text-link" href={HXGNY_CALENDAR_URL}>
              HXGNY school calendar
            </a>
            . That calendar is the authority for every date below; weeks with
            no school (breaks and holidays) are called out and skipped.
          </p>
        </section>

        <section className="section calendar-list-section">
          <ol className="calendar-list">
            {classSessions.map((session) => {
              const brk = breaksAfter.get(session.id);
              const isPublished = sessionsWithSlides.includes(session.id);
              return (
                <li key={session.id} className="calendar-item">
                  <div className="calendar-row">
                    <span className="calendar-session-id">{session.id}</span>
                    <span className="calendar-date">{formatSessionDate(session.date)}</span>
                    {isPublished ? (
                      <Link
                        className="calendar-title slides-link"
                        href={`/students/slides/${session.id.toLowerCase()}/`}
                      >
                        {session.title}
                      </Link>
                    ) : (
                      <span className="calendar-title">{session.title}</span>
                    )}
                  </div>
                  {brk ? (
                    <div className="calendar-break" role="note">
                      <span className="calendar-break-label">No class &mdash; {brk.label}</span>
                      <span className="calendar-break-dates">
                        {formatBreakRange(brk.startDate, brk.endDate)}
                      </span>
                    </div>
                  ) : null}
                </li>
              );
            })}
          </ol>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
