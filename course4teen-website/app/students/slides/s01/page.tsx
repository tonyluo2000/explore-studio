import type { Metadata } from "next";
import SiteHeader from "../../../components/SiteHeader";
import SiteFooter from "../../../components/SiteFooter";
import { classSessions, formatSessionDate } from "../../../../lib/calendar";

export const metadata: Metadata = {
  title: "S01 Slides · Explorer's Field Notes | Course4Teen",
  description:
    "Student slides for Course4Teen session S01, Explorer's Field Notes: the mission, what to try, and the checkpoints to hit.",
  alternates: { canonical: "/students/slides/s01/" },
};

const session = classSessions.find((s) => s.id === "S01")!;

const slides = [
  {
    kicker: "You've just arrived",
    heading: "Explore Every Object",
    body: (
      <>
        <p>
          You&rsquo;re stepping into an unfamiliar place, and the first thing
          any explorer does is start a field notebook. Today&rsquo;s three
          observations are the opening page of yours.
        </p>
        <p>
          <strong>Mission:</strong> <code>visit-all-classroom-objects</code>
        </p>
        <p>
          <strong>Learning target:</strong> Use <code>print(...)</code> and
          string literals to record three world observations, then repair
          mismatched quotation marks.
        </p>
      </>
    ),
  },
  {
    kicker: "Predict before running",
    heading: "Make a call before you test it",
    body: (
      <p>
        Write it down: &ldquo;I think ___ visible things will increase{" "}
        <code>Visited</code> because ___.&rdquo; Decide whether the player,
        Fern, the lantern, and the fountain should count.
      </p>
    ),
  },
  {
    kicker: "Core path",
    heading: "Write it, run it, walk it",
    body: (
      <ol className="slide-steps">
        <li>Open your <code>starter.py</code> file for this session.</li>
        <li>
          Replace its three strings with your own observations. Keep exactly
          three <code>print(...)</code> calls.
        </li>
        <li>Run the file and read what prints.</li>
        <li>
          <strong>Checkpoint:</strong> show three separate printed lines and
          explain what a string is.
        </li>
        <li>
          Field note reflection: reread your three observations and choose one
          detail that feels worth investigating next. There&rsquo;s no
          required answer &mdash; just pick the one that interests you.
        </li>
        <li>Launch the Trail for this mission from your terminal.</li>
        <li>
          Click the Trail window for focus. Move with WASD or the arrow keys
          and press <kbd>E</kbd> once near each world object.
        </li>
        <li>
          <strong>Checkpoint:</strong> compare the final visited count with
          your prediction.
        </li>
        <li>Close the Trail window. To retry: edit, save, run again.</li>
      </ol>
    ),
  },
  {
    kicker: "Debug checkpoint",
    heading: "Predict the error, then fix only the quotes",
    body: (
      <>
        <pre className="slide-code">
          <code>{`print("The lantern flickers near the fountain.')`}</code>
        </pre>
        <p>
          Evidence: explain where Python thinks the string begins and where
          it thinks the string ends.
        </p>
      </>
    ),
  },
  {
    kicker: "If you get stuck",
    heading: "Support and extension paths",
    body: (
      <>
        <p>
          <strong>Support:</strong> ask your teacher to demonstrate the Trail
          command. Report your three printed observations and watch which
          objects increase the visited count.
        </p>
        <p>
          <strong>Extension:</strong> add a fourth observation using matching
          single quotes. This does not change the mission.
        </p>
      </>
    ),
  },
  {
    kicker: "Using AI on this mission",
    heading: "Bounded questions, not full solutions",
    body: (
      <p>
        If you ask an AI tool for help, record your intent, your prediction,
        the exact bounded question you asked, the suggestion it gave, whether
        you accepted or rejected it, and your own explanation of the change.
        Do not paste whole files or ask AI for a complete solution.
      </p>
    ),
  },
  {
    kicker: "Close",
    heading: "Wrap up S01",
    body: (
      <p>
        Save your work and keep your course folder where you can find it next
        session. Understanding what you changed matters more than finishing
        every path during class &mdash; be ready to say which line you edited
        and why.
      </p>
    ),
  },
];

export default function S01SlidesPage() {
  return (
    <>
      <a className="skip-link" href="#main">Skip to content</a>
      <SiteHeader />
      <main id="main">
        <section className="section slides-hero">
          <p className="kicker">
            {session.id} &middot; {formatSessionDate(session.date)}
          </p>
          <h1>{session.title}</h1>
          <p className="calendar-lede">
            Student slides for session {session.id}. Use these to follow
            along in class or to recap what to try before next time.
          </p>
        </section>

        <section className="section slide-deck">
          {slides.map((slide) => (
            <article className="slide-card" key={slide.heading}>
              <p className="kicker">{slide.kicker}</p>
              <h2>{slide.heading}</h2>
              <div className="slide-body">{slide.body}</div>
            </article>
          ))}
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
