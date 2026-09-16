import type { Metadata } from "next";
import Link from "next/link";
import SiteHeader from "../../components/SiteHeader";
import SiteFooter from "../../components/SiteFooter";
import { classSessions, sessionsWithSlides } from "../../../lib/calendar";

export const metadata: Metadata = {
  title: "Student Slides | Course4Teen",
  description:
    "Web slides for Course4Teen students: session recaps, mission briefs, and checkpoints to follow along with in class.",
  alternates: { canonical: "/students/slides/" },
};

export default function StudentSlidesIndexPage() {
  return (
    <>
      <a className="skip-link" href="#main">Skip to content</a>
      <SiteHeader />
      <main id="main">
        <section className="section slides-hero">
          <p className="kicker">For students</p>
          <h1>Session slides.<br />Follow along, mission by mission.</h1>
          <p className="calendar-lede">
            Each session gets a short set of web slides you can revisit after
            class: the mission, what to try, and the checkpoints to hit.
            Slides go live as each session is taught.
          </p>
        </section>

        <section className="section calendar-list-section slides-list-section">
          <ol className="calendar-list">
            {classSessions.map((session) => {
              const isPublished = sessionsWithSlides.includes(session.id);
              return (
                <li key={session.id} className="calendar-item">
                  <div className="calendar-row slides-row">
                    <span className="calendar-session-id">{session.id}</span>
                    {isPublished ? (
                      <Link className="calendar-title slides-link" href={`/students/slides/${session.id.toLowerCase()}/`}>
                        {session.title}
                      </Link>
                    ) : (
                      <span className="calendar-title slides-pending">
                        {session.title} <em>&mdash; coming soon</em>
                      </span>
                    )}
                  </div>
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
