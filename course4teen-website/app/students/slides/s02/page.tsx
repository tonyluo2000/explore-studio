import type { Metadata } from "next";
import SiteHeader from "../../../components/SiteHeader";
import SiteFooter from "../../../components/SiteFooter";
import { classSessions, formatSessionDate } from "../../../../lib/calendar";

export const metadata: Metadata = {
  title: "S02 Slides · Place Your First Prop | Course4Teen",
  description:
    "Student slides for Course4Teen session S02, Place Your First Prop: the mission, what to try, and the checkpoints to hit.",
  alternates: { canonical: "/students/slides/s02/" },
};

const session = classSessions.find((s) => s.id === "S02")!;

const bridgeRows = [
  { python: "object_name", field: "name", result: "The label shown for your prop" },
  { python: "x", field: "x", result: "Left or right. Larger moves right." },
  { python: "y", field: "y", result: "Up or down. Larger moves down." },
  { python: "color", field: "color", result: "The named fill color" },
];

const supportedColors = [
  "red",
  "orange",
  "yellow",
  "green",
  "blue",
  "purple",
  "pink",
  "brown",
  "gold",
];

const slides = [
  {
    kicker: "Mission",
    heading: "Create Your First Object",
    body: (
      <>
        <p>
          <strong>Mission:</strong> <code>create-a-classroom-object</code>
        </p>
        <p>
          <strong>Learning target:</strong> Store a prop&rsquo;s name, integer
          x/y coordinates, and color in variables; predict its position; then
          adjust one coordinate from evidence.
        </p>
      </>
    ),
  },
  {
    kicker: "The bridge to the world",
    heading: "Your values become the prop",
    body: (
      <>
        <p>
          The object file &mdash; not <code>starter.py</code> &mdash; is what
          drives the shared world.
        </p>
        <div className="slide-map-wrap">
          <table className="slide-map">
            <caption className="slide-map-caption">
              What each value controls
            </caption>
            <thead>
              <tr>
                <th scope="col">Your Python value</th>
                <th scope="col">Object file field</th>
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
        <p>
          You copy the values across yourself. Python does not write or run the
          object file for you.
        </p>
      </>
    ),
  },
  {
    kicker: "Keep it visible",
    heading: "Stay in range, pick a real color",
    body: (
      <>
        <p>
          <strong>Lesson-safe range:</strong> <code>x</code> from 80 to 800,{" "}
          <code>y</code> from 100 to 500. This is a classroom visibility guide,
          not a new rule.
        </p>
        <p>
          <strong>Supported colors</strong> &mdash; lowercase, exactly as
          written:
        </p>
        <ul className="slide-swatches">
          {supportedColors.map((color) => (
            <li key={color}>
              <span
                className="slide-swatch"
                style={{ background: color }}
                aria-hidden="true"
              />
              <code>{color}</code>
            </li>
          ))}
        </ul>
      </>
    ),
  },
  {
    kicker: "Predict before running",
    heading: "Call the position before you see it",
    body: (
      <p>
        Sketch or describe where <code>(240, 180)</code> should appear. Then
        predict what increasing <code>x</code> by 100 will do &mdash; before you
        change anything.
      </p>
    ),
  },
  {
    kicker: "Core path",
    heading: "Set it, validate it, watch it move",
    body: (
      <ol className="slide-steps">
        <li>
          Personalize <code>object_name</code>, <code>x</code>, <code>y</code>,
          and <code>color</code> in your <code>starter.py</code>.
        </li>
        <li>Run the Python file and explain the type of each value.</li>
        <li>
          Put the same values in your object file, <code>compass.yaml</code>.
        </li>
        <li>Validate your package, then launch the Trail.</li>
        <li>
          <strong>Checkpoint:</strong> show <code>valid: ...</code> and point to
          the file that drives the world.
        </li>
        <li>
          Observe the position. Close the Trail, change either <code>x</code> or{" "}
          <code>y</code> once, validate, and relaunch. Interact with every world
          object.
        </li>
        <li>
          <strong>Checkpoint:</strong> state your prediction, the coordinate you
          changed, and the movement you observed.
        </li>
      </ol>
    ),
  },
  {
    kicker: "The two commands",
    heading: "Validate first. Always.",
    body: (
      <>
        <pre className="slide-code">
          <code>{`python starter.py
explore-package validate <your explorer package>`}</code>
        </pre>
        <p>Then launch the Trail for this mission:</p>
        <pre className="slide-code">
          <code>{`explore-package trail <class packages> <your package> \\
  --player "nova-character:nova" \\
  --mission-id "create-a-classroom-object" \\
  --name "S02 Place Your First Prop"`}</code>
        </pre>
        <p>
          If validation fails, fix only the first reported issue and try again.
        </p>
      </>
    ),
  },
  {
    kicker: "Debug checkpoint",
    heading: "Same number, wrong type",
    body: (
      <>
        <pre className="slide-code">
          <code>{`x: "240"`}</code>
        </pre>
        <p>
          Explain why this is the wrong type, then repair it without changing
          the number.
        </p>
      </>
    ),
  },
  {
    kicker: "When it looks wrong",
    heading: "Four things to check",
    body: (
      <ul className="slide-checks">
        <li>
          <strong>Color rejected?</strong> Use one lowercase name from the
          supported list.
        </li>
        <li>
          <strong>Indentation?</strong> Use spaces, and line up{" "}
          <code>name</code>, <code>x</code>, <code>y</code>, and{" "}
          <code>color</code>.
        </li>
        <li>
          <strong>Prop off screen?</strong> Return to the lesson-safe range,
          validate, relaunch.
        </li>
        <li>
          <strong>Still in the old spot?</strong> Close the old Trail, save the
          object file, validate, relaunch.
        </li>
      </ul>
    ),
  },
  {
    kicker: "If you get stuck",
    heading: "Support and extension paths",
    body: (
      <>
        <p>
          <strong>Support:</strong> keep the sample name and color, and change
          only one coordinate. Ask your teacher to check your indentation before
          you retype the file.
        </p>
        <p>
          <strong>Extension:</strong> make a second evidence-based coordinate
          adjustment &mdash; after predicting it.
        </p>
      </>
    ),
  },
  {
    kicker: "Using AI on this mission",
    heading: "Bounded questions, not full solutions",
    body: (
      <p>
        If you ask an AI tool for help, record your intent, your prediction, the
        exact bounded question you asked, the suggestion you tested, whether you
        accepted or rejected it, and your own explanation of the change. Do not
        paste whole files or ask AI for a complete solution.
      </p>
    ),
  },
  {
    kicker: "Close",
    heading: "Wrap up S02",
    body: (
      <p>
        Save your work and keep your course folder where you can find it next
        session. Be ready to say which value you changed and what moved because
        of it &mdash; understanding comes before rushing.
      </p>
    ),
  },
];

export default function S02SlidesPage() {
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
