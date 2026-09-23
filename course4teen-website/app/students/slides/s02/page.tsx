import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import SiteHeader from "../../../components/SiteHeader";
import SiteFooter from "../../../components/SiteFooter";
import NovaPixelScene from "../../../components/NovaPixelScene";
import CoordinateMap from "../../../components/CoordinateMap";
import S02TrailMap from "../../../components/S02TrailMap";
import { classSessions, formatSessionDate } from "../../../../lib/calendar";

export const metadata: Metadata = {
  title: "S02 Slides · Place Your First Prop | Course4Teen",
  description:
    "Student slides for Course4Teen session S02, Place Your First Prop: the mission, what to try, and the checkpoints to hit.",
  alternates: { canonical: "/students/slides/s02/" },
};

const session = classSessions.find((s) => s.id === "S02")!;

const bridgeRows = [
  {
    python: "object_name",
    field: "name",
    result: "Stored as your prop’s name. Names are not drawn on screen yet.",
  },
  { python: "x", field: "x", result: "Left or right. Larger moves right." },
  { python: "y", field: "y", result: "Up or down. Larger moves down." },
  { python: "color", field: "color", result: "The named fill color" },
];

const roles = [
  {
    kind: "Explorer",
    name: "Nova",
    text: "The character who explores. You move Nova on the Trail.",
  },
  {
    kind: "Companion",
    name: "Pixel",
    text: "Nova’s small, curious, careful robot friend.",
  },
  {
    kind: "Tool",
    name: "Moon Compass",
    text: "Something an explorer uses. Today you place it.",
  },
  {
    kind: "World object",
    name: "Crystal Lantern",
    text: "Something that is part of the world. The trail’s destination.",
  },
];

type Wiring = "trail" | "card" | "plan" | "stored";

const wiringLabel: Record<Wiring, string> = {
  trail: "Changes the Trail",
  card: "Card only",
  plan: "Plan only",
  stored: "Stored, not drawn",
};

const valueRows: { values: string[]; file: string; wiring: Wiring }[] = [
  {
    values: ["explorer_name", "looks_like", "personality", "favorite_subject"],
    file: "explorer.py",
    wiring: "card",
  },
  {
    values: ["companion_name", "companion_kind", "personality", "specialty"],
    file: "companion.py",
    wiring: "card",
  },
  { values: ["future_ability"], file: "companion.py", wiring: "plan" },
  { values: ["x", "y", "color"], file: "compass.yaml", wiring: "trail" },
  { values: ["name"], file: "compass.yaml", wiring: "stored" },
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

type Slide = {
  kicker: string;
  heading: string;
  body: ReactNode;
  hero?: boolean;
};

const slides: Slide[] = [
  {
    kicker: "Nova & Pixel",
    heading: "The Adventure Continues",
    hero: true,
    body: (
      <>
        <NovaPixelScene />
        <p className="slide-lede">
          Today: use Python to start creating your own explorer and companion.
          Nova and Pixel are the class examples.
        </p>
        <pre className="slide-code">
          <code>{`explorer_name = "Nova"
companion_name = "Pixel"`}</code>
        </pre>
      </>
    ),
  },
  {
    kicker: "Share-out",
    heading: "Who will explore your world?",
    body: (
      <>
        <p>Share the explorer and companion you imagined after Session 1:</p>
        <ul className="slide-checks">
          <li>
            Your explorer&rsquo;s name, appearance, personality, and one interest or
            favorite subject.
          </li>
          <li>
            Your companion&rsquo;s name, kind, personality, and one specialty or
            interest.
          </li>
          <li>
            One thing you eventually want your companion to do: fly, scan rocks,
            identify animals, find hidden paths, recognize constellations&hellip;
          </li>
        </ul>
        <p>
          <strong>It cannot do all of that yet.</strong> As you learn more
          Python, you&rsquo;ll teach it how.
        </p>
      </>
    ),
  },
  {
    kicker: "Four kinds of things",
    heading: "Explorer, companion, tool, world object",
    body: (
      <>
        <ul className="role-grid">
          {roles.map((role) => (
            <li key={role.kind} className="role-card">
              <span className="role-kind">{role.kind}</span>
              <strong>{role.name}</strong>
              <span>{role.text}</span>
            </li>
          ))}
        </ul>
        <p>
          Pixel is in today&rsquo;s Trail and says hello when you press{" "}
          <kbd>E</kbd> nearby. Pixel stays where it was placed: it does not
          follow Nova or make its own decisions yet.
        </p>
      </>
    ),
  },
  {
    kicker: "Your trail today",
    heading: "Start, compass, lantern",
    body: <S02TrailMap />,
  },
  {
    kicker: "Explorers need tools",
    heading: "Your first expedition tool",
    body: (
      <>
        <p>
          The Moon Compass is the expedition&rsquo;s first instrument, and{" "}
          <strong>you</strong> decide where it lives. The Crystal Lantern is
          already in the world and marks the end of the trail. Put the compass
          somewhere an explorer would actually notice it and want to reach on
          the way.
        </p>
        <p>
          <strong>Mission:</strong> <code>create-a-classroom-object</code>
        </p>
        <p>
          <strong>Learning target:</strong> Store names, integer x/y
          coordinates, and a color in variables; explain which values are
          strings and which are integers; predict an object&rsquo;s position;
          then adjust one coordinate from evidence.
        </p>
      </>
    ),
  },
  {
    kicker: "Python first",
    heading: "Variables and values",
    body: (
      <>
        <pre className="slide-code">
          <code>{`object_name = "Moon Compass"
x = 240
y = 180
color = "purple"`}</code>
        </pre>
        <ul className="slide-checks">
          <li>
            <code>x = 240</code> means: store the integer value <code>240</code>{" "}
            under the variable name <code>x</code>.
          </li>
          <li>
            <strong>Assignment</strong> (<code>=</code>) stores a value under a
            name.
          </li>
          <li>
            <strong>Strings</strong> are text in quotes:{" "}
            <code>&quot;Moon Compass&quot;</code>, <code>&quot;purple&quot;</code>.
          </li>
          <li>
            <strong>Integers</strong> are whole numbers with no quotes:{" "}
            <code>240</code>, <code>180</code>.
          </li>
        </ul>
        <div className="type-compare">
          <div>
            <pre className="slide-code"><code>x = 240</code></pre>
            <p>An integer. Python can calculate with it.</p>
          </div>
          <div>
            <pre className="slide-code"><code>{`x = "240"`}</code></pre>
            <p>A string. Same digits, but it is text.</p>
          </div>
        </div>
      </>
    ),
  },
  {
    kicker: "Yours to keep",
    heading: "Make your own world folder",
    body: (
      <>
        <p>
          Your explorer and companion belong to you, so they live in your own
          folder, not inside the course folder. From the course folder, run:
        </p>
        <pre className="slide-code">
          <code>python3 make-my-world.py</code>
        </pre>
        <p>
          Open <code>my-explore-world/explorer.py</code> and{" "}
          <code>companion.py</code>. Replace every <code>TODO</code> with concrete
          choices for your own Explorer and Companion: name, appearance or kind,
          personality, interest or specialty, and one <code>future_ability</code>.
          Nova and Pixel are examples, not required answers. The future ability
          is planning text only. Keep the quotation marks.
        </p>
        <div className="slide-map-wrap">
          <table className="slide-map slide-map-compact">
            <caption className="slide-map-caption">Practice vs. yours</caption>
            <tbody>
              <tr>
                <th scope="row"><code>starter.py</code></th>
                <td>Practice today&rsquo;s Python.</td>
              </tr>
              <tr>
                <th scope="row"><code>my-explore-world/</code></th>
                <td>
                  Your characters and <code>projects/moon-compass/</code>.
                  Course updates never replace them.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </>
    ),
  },
  {
    kicker: "Designed by you",
    heading: "These Python values describe your explorer",
    body: (
      <>
        <div className="card-compare">
          <div>
            <pre className="slide-code">
              <code>{`explorer_name = "Comet"
looks_like = "a bright orange scarf"
personality = "brave"
favorite_subject = "volcanoes"`}</code>
            </pre>
            <p className="card-arrow" aria-hidden="true">
              run it &darr;
            </p>
            <pre className="id-card" aria-label="Printed Explorer Card">
              <code>{`MY EXPLORER CARD  (designed by me)
Name:          Comet
Looks like:    a bright orange scarf
Personality:   brave
Interested in: volcanoes`}</code>
            </pre>
          </div>
          <div>
            <pre className="slide-code">
              <code>{`companion_name = "Moss"
companion_kind = "tiny rock turtle"
personality = "patient"
specialty = "finding shiny stones"
future_ability = "light up dark caves"`}</code>
            </pre>
            <p className="card-arrow" aria-hidden="true">
              run it &darr;
            </p>
            <pre className="id-card" aria-label="Printed Companion Card">
              <code>{`MY COMPANION CARD  (designed by me)
Name:        Moss
Kind:        tiny rock turtle
Personality: patient
Specialty:   finding shiny stones
PLAN for later, not built yet:
  Someday it will: light up dark caves`}</code>
            </pre>
          </div>
        </div>
        <p>
          Comet and Moss are made-up samples. Your cards show <strong>your</strong>{" "}
          values.
        </p>
        <div className="slide-map-wrap">
          <table className="slide-map slide-map-compact">
            <caption className="slide-map-caption">What each value does today</caption>
            <thead>
              <tr>
                <th scope="col">Values</th>
                <th scope="col">Changes the Trail?</th>
              </tr>
            </thead>
            <tbody>
              {valueRows.map((row) => (
                <tr key={`${row.file}-${row.values.join("-")}`}>
                  <th scope="row">
                    <span className="wiring-values">
                      {row.values.map((value) => (
                        <code key={value}>{value}</code>
                      ))}
                    </span>
                    <span className="wiring-file">
                      in <code>{row.file}</code>
                    </span>
                  </th>
                  <td>
                    <span className={`wiring-badge wiring-${row.wiring}`}>
                      {wiringLabel[row.wiring]}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </>
    ),
  },
  {
    kicker: "Coordinates",
    heading: "Numbers that describe a position",
    body: (
      <>
        <CoordinateMap />
        <p>
          <code>x</code> and <code>y</code> are integers. A bigger{" "}
          <code>x</code> moves right. A bigger <code>y</code> moves{" "}
          <strong>down</strong>.
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
    heading: "Where should this instrument go, and why?",
    body: (
      <p>
        Sketch or describe where <code>(240, 180)</code> should appear so an
        explorer passing through would notice it. Then predict what increasing{" "}
        <code>x</code> by 100 will do &mdash; before you change anything.
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
          Put the same values in your student-owned file,{" "}
          <code>../my-explore-world/projects/moon-compass/objects/compass.yaml</code>.
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
          <code>{`python lessons/sessions/s02/student/starter.py
explore-package validate ../my-explore-world/projects/moon-compass`}</code>
        </pre>
        <p>Then launch the Trail for this mission:</p>
        <pre className="slide-code">
          <code>{`explore-package trail <class packages> ../my-explore-world/projects/moon-compass \\
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
    kicker: "What we discovered",
    heading: "Coordinates in our world",
    body: (
      <>
        <div className="discovery-grid">
          <div className="discovery-card discovery-fiction">
            <p className="discovery-tag">In Nova&rsquo;s world &middot; fiction</p>
            <p>The Moon Compass is a fictional exploration tool.</p>
          </div>
          <div className="discovery-card discovery-fact">
            <p className="discovery-tag">In our world &middot; fact</p>
            <p>
              Maps use coordinates too: latitude and longitude. A magnetic
              compass lines up with Earth&rsquo;s magnetic field.
            </p>
          </div>
        </div>
        <p>
          <Link className="text-link" href="/students/learn/s02/#discovery-heading">
            Read the full discovery &rarr;
          </Link>
        </p>
      </>
    ),
  },
  {
    kicker: "Exit check",
    heading: "Three quick answers",
    body: (
      <ul className="slide-checks">
        <li>
          <strong>Python:</strong> What is a variable? Which values were
          strings? Which were integers? What does changing <code>x</code> do?
        </li>
        <li>
          <strong>Your world:</strong> What are your Explorer&rsquo;s name,
          appearance, personality, and interest? What are your Companion&rsquo;s
          name, kind, personality, and specialty? What future ability do you
          want to program later?
        </li>
        <li>
          <strong>Discovery:</strong> What do coordinates describe? How is the
          fictional Moon Compass different from a real magnetic compass?
        </li>
      </ul>
    ),
  },
  {
    kicker: "Looking ahead",
    heading: "A static instrument, for now",
    body: (
      <p>
        Today&rsquo;s Moon Compass sits where you placed it and does nothing
        else yet. Next session, it gains its own clue and reveal, becoming an
        active part of the expedition story.
      </p>
    ),
  },
  {
    kicker: "Close",
    heading: "Wrap up S02",
    body: (
      <>
        <p>
          Save your work in <code>my-explore-world</code> and keep both folders
          where you can find them next session. Be ready to say which value you
          changed and what moved because of it &mdash; understanding comes before
          rushing.
        </p>
        <p>
          <Link className="text-link" href="/students/learn/s02/">
            What we learned in Python today &rarr;
          </Link>
        </p>
      </>
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
