import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import SiteHeader from "../../../components/SiteHeader";
import SiteFooter from "../../../components/SiteFooter";
import { classSessions, formatSessionDate } from "../../../../lib/calendar";

export const metadata: Metadata = {
  title: "S03 Slides · Make the World React | Course4Teen",
  description:
    "Student slides for Course4Teen session S03, Make the World React: f-strings, near and interaction messages, and the checkpoints to hit.",
  alternates: { canonical: "/students/slides/s03/" },
};

const session = classSessions.find((s) => s.id === "S03")!;

const variableRows = [
  { name: "object_name", holds: "The object’s name: \"Moon Compass\"." },
  { name: "near_message", holds: "Your clue. Built with an f-string that uses object_name." },
  { name: "interacted_message", holds: "Your reveal. Also built with an f-string." },
];

const bridgeRows = [
  { python: "near_message", field: "when_near", result: "Appears when the player approaches" },
  { python: "interacted_message", field: "when_interacted", result: "Appears after E is pressed nearby" },
];

const trailCommand = `explore-package trail \\
  examples/explorer-packages/nova-character \\
  lessons/sessions/s03/student/explorer-package \\
  --player "nova-character:nova" \\
  --mission-id "make-your-object-respond" \\
  --name "S03 Make the World React"`;

type Slide = {
  kicker: string;
  heading: string;
  body: ReactNode;
  hero?: boolean;
};

const slides: Slide[] = [
  {
    kicker: "The Moonlit expedition begins",
    heading: "Make the World React",
    hero: true,
    body: (
      <>
        <p className="slide-lede">
          Last session your Moon Compass sat where you placed it. Today it
          gets a clue and a reveal, and you write both.
        </p>
        <pre className="slide-code">
          <code>{`near_message = f"The {object_name} needle trembles toward the dark trees."`}</code>
        </pre>
      </>
    ),
  },
  {
    kicker: "Today's mission",
    heading: "M03 · Make It Respond",
    body: (
      <>
        <p>
          <strong>Mission:</strong> <code>make-your-object-respond</code>
        </p>
        <p>
          <strong>Learning target:</strong> Construct an f-string message from
          an object-name variable and predict which player event reveals each
          authored response.
        </p>
        <p>
          The Moon Compass is hiding a secret. <strong>You choose</strong> what
          it is. Your nearby clue hints at it; your interaction line reveals it.
        </p>
      </>
    ),
  },
  {
    kicker: "Recap from S02",
    heading: "Variables and strings",
    body: (
      <>
        <pre className="slide-code">
          <code>{`object_name = "Moon Compass"
print(object_name)`}</code>
        </pre>
        <ul className="slide-checks">
          <li>
            A <strong>variable</strong> is a name that stores a value.
          </li>
          <li>
            A <strong>string</strong> is text inside matching quotation marks.
          </li>
          <li>
            <code>print(object_name)</code> shows the stored value:{" "}
            <code>Moon Compass</code>.
          </li>
        </ul>
      </>
    ),
  },
  {
    kicker: "New today",
    heading: "f-strings",
    body: (
      <>
        <p>
          Put an <code>f</code> right before the opening quote, and Python
          lets you place variables inside the string with curly braces.
        </p>
        <div className="type-compare">
          <div>
            <pre className="slide-code"><code>{`"The {object_name} glows."`}</code></pre>
            <p>A plain string. The braces are printed as typed.</p>
          </div>
          <div>
            <pre className="slide-code"><code>{`f"The {object_name} glows."`}</code></pre>
            <p>An f-string. Python fills in the value.</p>
          </div>
        </div>
      </>
    ),
  },
  {
    kicker: "Three names to know",
    heading: "object_name, near_message, interacted_message",
    body: (
      <div className="slide-map-wrap">
        <table className="slide-map">
          <caption className="slide-map-caption">Today&rsquo;s variables</caption>
          <tbody>
            {variableRows.map((row) => (
              <tr key={row.name}>
                <th scope="row">
                  <code>{row.name}</code>
                </th>
                <td>{row.holds}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    ),
  },
  {
    kicker: "How braces work",
    heading: "Braces substitute a value",
    body: (
      <>
        <pre className="slide-code">
          <code>{`object_name = "Moon Compass"
near_message = f"The {object_name} glows."
print(near_message)`}</code>
        </pre>
        <pre className="slide-code slide-output">
          <code>The Moon Compass glows.</code>
        </pre>
        <p>
          <strong>Checkpoint:</strong> point to the braces and explain what
          value appears there.
        </p>
      </>
    ),
  },
  {
    kicker: "Two different events",
    heading: "Move near vs. press E",
    body: (
      <>
        <ul className="slide-checks">
          <li>
            <strong>Move near:</strong> walk up to the compass without pressing
            anything. The <strong>near</strong> message appears: your clue.
          </li>
          <li>
            <strong>Press E nearby:</strong> interact with the compass. The{" "}
            <strong>interacted</strong> message appears: your reveal.
          </li>
        </ul>
        <p>
          Same object, two events, two different messages. Approach first,
          record what you see, then press <kbd>E</kbd>.
        </p>
      </>
    ),
  },
  {
    kicker: "Your story choice",
    heading: "Choose a secret, write a clue",
    body: (
      <>
        <p>
          What is the Moon Compass hiding? A lantern, a fork in the trail, a
          clearing, or an idea of your own.
        </p>
        <ul className="slide-checks">
          <li>
            <strong>The clue</strong> (near) hints at the secret without giving
            it away: a direction, a feeling, or an object.
          </li>
          <li>
            <strong>The reveal</strong> (interacted) tells what the secret is.
          </li>
          <li>
            If your clue simply repeats the reveal, make it more indirect.
          </li>
        </ul>
      </>
    ),
  },
  {
    kicker: "Predict before interacting",
    heading: "Say it before you see it",
    body: (
      <>
        <p>Complete this sentence before you run the Trail:</p>
        <p className="slide-lede">
          &ldquo;Moving near will show ___; pressing E will show ___.&rdquo;
        </p>
        <p>
          With a partner: read your clue aloud and have them guess the reveal{" "}
          <strong>before either of you presses E</strong>. No partner? Write
          your reveal prediction on paper first.
        </p>
      </>
    ),
  },
  {
    kicker: "Python first",
    heading: "The starter",
    body: (
      <>
        <pre className="slide-code">
          <code>{`object_name = "Moon Compass"
near_message = f"{object_name}"  # TODO: add a nearby clue inside this f-string.
interacted_message = f"The {object_name} points past the trees to a guide's lantern!"

print(near_message)
print(interacted_message)`}</code>
        </pre>
        <pre className="slide-code">
          <code>python lessons/sessions/s03/student/starter.py</code>
        </pre>
        <p>Before you change anything, it prints:</p>
        <pre className="slide-code slide-output">
          <code>{`Moon Compass
The Moon Compass points past the trees to a guide's lantern!`}</code>
        </pre>
        <p>
          The first line is only the name. That is on purpose: the clue is
          yours to write.
        </p>
      </>
    ),
  },
  {
    kicker: "Core path",
    heading: "Clue, reveal, run",
    body: (
      <ol className="slide-steps">
        <li>Choose your secret: what the Moon Compass&rsquo;s clue is hiding.</li>
        <li>
          Expand <code>near_message = f&quot;{"{object_name}"}&quot;</code> into a
          complete nearby clue. Keep <code>{"{object_name}"}</code> inside the
          f-string.
        </li>
        <li>
          Write your own reveal line for <code>interacted_message</code>, then
          run the file.
        </li>
        <li>
          <strong>Checkpoint:</strong> both printed lines now include the object
          name and your story text.
        </li>
      </ol>
    ),
  },
  {
    kicker: "The bridge to the world",
    heading: "Python text becomes YAML text",
    body: (
      <>
        <div className="slide-map-wrap">
          <table className="slide-map">
            <caption className="slide-map-caption">Where each message goes</caption>
            <thead>
              <tr>
                <th scope="col">Python value</th>
                <th scope="col">YAML field</th>
                <th scope="col">What you see</th>
              </tr>
            </thead>
            <tbody>
              {bridgeRows.map((row) => (
                <tr key={row.python}>
                  <th scope="row">
                    <code>{row.python}</code>
                  </th>
                  <td>
                    <code>{row.field}</code>
                  </td>
                  <td>{row.result}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p>Copy only the final message text into the object file:</p>
        <pre className="slide-code">
          <code>{`# lessons/sessions/s03/student/explorer-package/objects/compass.yaml
when_near: "The Moon Compass needle trembles toward the dark trees."
when_interacted: "The Moon Compass points past the trees to a guide's lantern!"`}</code>
        </pre>
        <p>
          YAML drives the world. Python helps you compose and check the text.
          The YAML file gets plain text, with no braces.
        </p>
      </>
    ),
  },
  {
    kicker: "Validate first",
    heading: "Check the package",
    body: (
      <>
        <pre className="slide-code">
          <code>explore-package validate lessons/sessions/s03/student/explorer-package</code>
        </pre>
        <p>
          Look for <code>valid: ...</code>. If validation fails, fix only the
          first reported issue and try again.
        </p>
      </>
    ),
  },
  {
    kicker: "Launch the Trail",
    heading: "See both events",
    body: (
      <>
        <pre className="slide-code">
          <code>{trailCommand}</code>
        </pre>
        <ol className="slide-steps">
          <li>Approach without pressing E. Record the near message.</li>
          <li>Press E. Record the interaction message.</li>
          <li>
            Compare your partner&rsquo;s prediction with the actual reveal.
          </li>
          <li>M03 completes after you interact with every world object.</li>
        </ol>
        <p>
          Today&rsquo;s Trail is the same painted Moon Meadow as S02. What
          changes today is the text your compass shows. If you see a plain dark
          Trail with a rectangle Compass, your course tools are out of date
          &mdash; tell your teacher.
        </p>
      </>
    ),
  },
  {
    kicker: "Deliberate debugging",
    heading: "Edit, predict, run, restore",
    body: (
      <>
        <ol className="slide-steps">
          <li>Save your working line somewhere in your notes.</li>
          <li>
            Temporarily remove the closing <code>{"}"}</code> after{" "}
            <code>object_name</code>:
          </li>
        </ol>
        <pre className="slide-code">
          <code>{`near_message = f"The {object_name needle begins to shimmer."`}</code>
        </pre>
        <ol className="slide-steps" start={3}>
          <li>Predict the error before running Python.</li>
          <li>
            Run and read the final error line. It starts with{" "}
            <code>SyntaxError</code>.
          </li>
          <li>Restore the saved working line and rerun successfully.</li>
        </ol>
      </>
    ),
  },
  {
    kicker: "Reasoning check",
    heading: "What if the fields were swapped?",
    body: (
      <>
        <pre className="slide-code">
          <code>{`when_near: "The Moon Compass points past the trees to a guide's lantern!"
when_interacted: "The Moon Compass needle trembles toward the dark trees."`}</code>
        </pre>
        <p>
          Both values are valid text, so the package can still pass
          validation. Predict what a player would see.
        </p>
        <p>
          <strong>Answer:</strong> the reveal shows up just by walking near,
          and the clue only appears after pressing E. The story is spoiled.
          Fix it by putting each message back in its matching field.
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
          <strong>Support:</strong> start with{" "}
          <code>near_message = f&quot;The {"{object_name}"} glows.&quot;</code>, then
          replace <code>glows</code> with your own clue. Ask the teacher to
          identify the field, not write the message.
        </p>
        <p>
          <strong>Extension:</strong> write a second, harder clue that
          foreshadows the same reveal with less detail, so a partner has to
          think longer before predicting it. Keep exactly the two existing
          response fields.
        </p>
      </>
    ),
  },
  {
    kicker: "Using AI on this mission",
    heading: "Bounded questions, not full solutions",
    body: (
      <p>
        Write both of your own lines first. AI may suggest wording or explain
        one brace or field mismatch. It may not write either message, choose
        your secret, or invent a new event. Record your intent, prediction,
        exact question, suggestion tested, accepted or rejected change, and
        your own explanation.
      </p>
    ),
  },
  {
    kicker: "Exit check",
    heading: "Three quick answers",
    body: (
      <ul className="slide-checks">
        <li>
          <strong>f-strings:</strong> In your <code>near_message</code>, what
          value appears where the braces are?
        </li>
        <li>
          <strong>Events:</strong> Which message appears when you move near?
          Which appears when you press E? Did your prediction match?
        </li>
        <li>
          <strong>Debugging:</strong> What happened when the closing brace was
          missing? What would a player see if the two YAML messages were
          swapped?
        </li>
      </ul>
    ),
  },
  {
    kicker: "Looking ahead",
    heading: "S04 · Introduce a Character",
    body: (
      <p>
        Your Moon Compass&rsquo;s clue points toward someone. Next session, the
        expedition meets a guide who needs your help, and you write a Python
        function that gives the guide a voice.
      </p>
    ),
  },
  {
    kicker: "Close",
    heading: "Wrap up S03",
    body: (
      <>
        <p>
          Save your files. Be ready to explain the braces in your f-string and
          which event shows each message. A correct explanation matters more
          than finishing every step.
        </p>
        <p>
          <Link className="text-link" href="/students/learn/s03/">
            What we learned in Python today &rarr;
          </Link>
        </p>
      </>
    ),
  },
];

export default function S03SlidesPage() {
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
            <article className={slide.hero ? "slide-card slide-hero-card" : "slide-card"} key={slide.heading}>
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
