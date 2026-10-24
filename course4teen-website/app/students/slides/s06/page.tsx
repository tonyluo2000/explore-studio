import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import SiteHeader from "../../../components/SiteHeader";
import SiteFooter from "../../../components/SiteFooter";
import JourneyContext from "../../../components/JourneyContext";
import { classSessions, formatSessionDate } from "../../../../lib/calendar";

const session = classSessions.find((s) => s.id === "S06")!;
const nextSession = classSessions.find((s) => s.id === "S07")!;

export const metadata: Metadata = {
  title: `${session.id} Slides · ${session.title} | Course4Teen`,
  description: `Student slides for Course4Teen session ${session.id}, ${session.title}: exactly three object dictionaries in one list, one plain for loop, key lookup, and transfer to package YAML.`,
  alternates: { canonical: "/students/slides/s06/" },
};

const trailCommand = `explore-package trail \\
  examples/explorer-packages/nova-character \\
  lessons/sessions/s06/student/explorer-package \\
  --player "nova-character:nova" \\
  --mission-id "build-an-object-collection" \\
  --name "S06 Build a Themed Collection"`;

type Slide = {
  kicker: string;
  heading: string;
  body: ReactNode;
  hero?: boolean;
};

const slides: Slide[] = [
  {
    kicker: "The Moonlit trail continues",
    heading: session.title,
    hero: true,
    body: (
      <>
        <p className="slide-lede">
          Build three related breadcrumb markers in order: <strong>Sun Seed</strong>,{" "}
          <strong>Rain Bell</strong>, then <strong>Wind Flower</strong>. Plan them as
          Python records, transfer the values to YAML, and follow the trail in the world.
        </p>
        <pre className="slide-code">
          <code>{`objects = [{...}, {...}, {...}]`}</code>
        </pre>
      </>
    ),
  },
  {
    kicker: "Today’s mission",
    heading: "M06 · Build a Curious Collection",
    body: (
      <>
        <p>
          <strong>Mission:</strong> <code>build-an-object-collection</code>
        </p>
        <p>
          <strong>Learning target:</strong> Represent exactly three related objects as
          dictionaries in one list, trace the first iteration of one plain{" "}
          <code>for</code> loop, and print a design inventory before transferring the
          values to package YAML.
        </p>
        <p>M06 is complete only after you interact with all three objects.</p>
      </>
    ),
  },
  {
    kicker: "One object",
    heading: "A dictionary is one record",
    body: (
      <>
        <p>
          A <strong>dictionary</strong> keeps the properties of one object together as
          key-value pairs.
        </p>
        <pre className="slide-code">
          <code>{`{"name": "Sun Seed", "x": 180, "y": 180, "color": "gold"}`}</code>
        </pre>
        <ul className="slide-checks">
          <li>The keys are <code>&quot;name&quot;</code>, <code>&quot;x&quot;</code>, <code>&quot;y&quot;</code>, and <code>&quot;color&quot;</code>.</li>
          <li>Each key has one value after its colon.</li>
          <li>One complete dictionary plans one world object.</li>
        </ul>
      </>
    ),
  },
  {
    kicker: "Three objects",
    heading: "A list is an ordered collection of records",
    body: (
      <>
        <pre className="slide-code">
          <code>{`objects = [
    {"name": "Sun Seed", "x": 180, "y": 180, "color": "gold"},
    {"name": "Rain Bell", "x": 380, "y": 300, "color": "blue"},
    {"name": "Wind Flower", "x": 620, "y": 420, "color": "pink"},
]`}</code>
        </pre>
        <p>
          Keep <strong>exactly three</strong> dictionaries. Their list order is the
          breadcrumb order: Sun Seed &rarr; Rain Bell &rarr; Wind Flower.
        </p>
      </>
    ),
  },
  {
    kicker: "Read one property",
    heading: "Look up a value by key",
    body: (
      <>
        <pre className="slide-code">
          <code>{`object_record["x"]`}</code>
        </pre>
        <p>
          The square brackets ask the current dictionary for the value stored under{" "}
          <code>&quot;x&quot;</code>. For the Sun Seed record, the result is <code>180</code>.
        </p>
        <p>
          The spelling must match the key exactly. Python does not guess a missing or
          differently spelled property.
        </p>
      </>
    ),
  },
  {
    kicker: "Repeat one block",
    heading: "One plain for loop",
    body: (
      <>
        <pre className="slide-code">
          <code>{`for object_record in objects:
    print(
        object_record["name"],
        object_record["x"],
        object_record["y"],
        object_record["color"],
    )`}</code>
        </pre>
        <p>
          Python takes each dictionary from <code>objects</code> in order, gives it the
          temporary name <code>object_record</code>, and runs the same indented print.
        </p>
      </>
    ),
  },
  {
    kicker: "Predict before running",
    heading: "Trace the first iteration",
    body: (
      <>
        <p>Do not run the starter yet. Fill in this trace on paper:</p>
        <pre className="slide-code slide-output">
          <code>{`object_record is the record named: __________
object_record["x"] is: __________
the first printed line will be: ______________________________`}</code>
        </pre>
        <p>
          Then circle any duplicate name or coordinate and any missing property you
          predict will cause trouble.
        </p>
      </>
    ),
  },
  {
    kicker: "Python first",
    heading: "Complete the starter",
    body: (
      <>
        <pre className="slide-code">
          <code>{`objects = [
    {"name": "Sun Seed", "x": 180, "y": 180, "color": "gold"},
    {"name": "Rain Bell", "x": 380, "y": 300, "color": "blue"},
    {"name": "TODO: third garden object", "x": 620, "y": 420, "color": "green"},
]`}</code>
        </pre>
        <ol className="slide-steps">
          <li>Check your first-iteration trace.</li>
          <li>Replace only the third record&rsquo;s TODO name and choose its color.</li>
          <li>Keep all four properties in every record.</li>
          <li>Run <code>python lessons/sessions/s06/student/starter.py</code>.</li>
        </ol>
      </>
    ),
  },
  {
    kicker: "Checkpoint",
    heading: "Three inventory lines",
    body: (
      <>
        <p>A completed canonical example prints:</p>
        <pre className="slide-code slide-output">
          <code>{`Sun Seed 180 180 gold
Rain Bell 380 300 blue
Wind Flower 620 420 pink`}</code>
        </pre>
        <p>
          Point to one lookup in your loop and explain which dictionary supplies its
          value on the first iteration.
        </p>
      </>
    ),
  },
  {
    kicker: "Deliberate debugging",
    heading: "Find the missing y property",
    body: (
      <>
        <pre className="slide-code">
          <code>{`broken_record = {
    "name": "Wind Flower",
    "x": 520,
    "color": "pink",
}

print(broken_record["y"])`}</code>
        </pre>
        <pre className="slide-code slide-output">
          <code>KeyError: &apos;y&apos;</code>
        </pre>
        <p>
          The lookup asks for <code>&quot;y&quot;</code>, but the record has no such key. Add an
          integer <code>y</code> property before reading it, then rerun successfully.
        </p>
      </>
    ),
  },
  {
    kicker: "Keep the boundary clear",
    heading: "Python plans; YAML drives the Trail",
    body: (
      <>
        <div className="slide-map-wrap">
          <table className="slide-map">
            <caption className="slide-map-caption">Transfer the intended values</caption>
            <thead>
              <tr><th scope="col">Python record</th><th scope="col">Package file</th><th scope="col">Visible object</th></tr>
            </thead>
            <tbody>
              <tr><th scope="row"><code>objects[0]</code></th><td><code>objects/sun-seed.yaml</code></td><td>Sun Seed</td></tr>
              <tr><th scope="row"><code>objects[1]</code></th><td><code>objects/rain-bell.yaml</code></td><td>Rain Bell</td></tr>
              <tr><th scope="row"><code>objects[2]</code></th><td><code>objects/wind-flower.yaml</code></td><td>Wind Flower</td></tr>
            </tbody>
          </table>
        </div>
        <p>
          Python never executes from the package. The validated YAML values are what
          the runtime loads into the visible world.
        </p>
      </>
    ),
  },
  {
    kicker: "Package rules",
    heading: "Three distinct breadcrumb markers",
    body: (
      <ul className="slide-checks">
        <li>Keep exactly three package objects.</li>
        <li>Give them distinct names, positions, colors, near responses, and interaction responses.</li>
        <li>Make Sun Seed lead toward Rain Bell, and Rain Bell lead toward Wind Flower.</li>
        <li>Let Wind Flower point toward a gate hidden in the sky.</li>
      </ul>
    ),
  },
  {
    kicker: "Validate before launching",
    heading: "Ask the package validator",
    body: (
      <>
        <pre className="slide-code">
          <code>explore-package validate lessons/sessions/s06/student/explorer-package</code>
        </pre>
        <pre className="slide-code slide-output"><code>valid: starlight-garden 0.1.0</code></pre>
        <p>
          If validation fails, read its file and field location. Repair the YAML error
          separately from the Python <code>KeyError</code> exercise.
        </p>
      </>
    ),
  },
  {
    kicker: "Launch M06",
    heading: "Open the standard Trail",
    body: (
      <>
        <pre className="slide-code"><code>{trailCommand}</code></pre>
        <p>
          This mission uses the standard, plain Trail presentation. Nova and the three
          package objects are enough; there is no NPC or lantern dependency.
        </p>
      </>
    ),
  },
  {
    kicker: "Play the collection",
    heading: "Interact with all three objects",
    body: (
      <ol className="slide-steps">
        <li>Move Nova near Sun Seed and press <strong>E</strong>.</li>
        <li>Follow its breadcrumb to Rain Bell and press <strong>E</strong>.</li>
        <li>Follow Rain Bell to Wind Flower and press <strong>E</strong>.</li>
        <li>Confirm the mission state changes to <strong>Complete</strong> only after all three visits.</li>
      </ol>
    ),
  },
  {
    kicker: "Scope guard",
    heading: "One list, one loop, three records",
    body: (
      <>
        <p>Today&rsquo;s solution has a deliberately small shape:</p>
        <ul className="slide-checks">
          <li>No list comprehension.</li>
          <li>No nested loop.</li>
          <li>No second loop.</li>
          <li>No fourth object.</li>
        </ul>
        <p>
          Strengthen the three existing response strings if you finish early; do not add
          another mechanic.
        </p>
      </>
    ),
  },
  {
    kicker: "Explain your model",
    heading: "Checkpoint before close",
    body: (
      <ul className="slide-checks">
        <li><strong>Dictionary:</strong> Which properties belong to one record?</li>
        <li><strong>List:</strong> Why does the order of the three records matter?</li>
        <li><strong>Loop:</strong> What changes from the first iteration to the second?</li>
        <li><strong>Boundary:</strong> Which file plans values, and which files drive the Trail?</li>
        <li><strong>Mission:</strong> Why is M06 incomplete after only two interactions?</li>
      </ul>
    ),
  },
  {
    kicker: "Looking ahead",
    heading: `${nextSession.id} · ${nextSession.title}`,
    body: (
      <p>
        That&rsquo;s the next session on the class calendar. For now, keep the final
        breadcrumb&rsquo;s skyward clue as story only.
      </p>
    ),
  },
  {
    kicker: "Close",
    heading: "Wrap up S06",
    body: (
      <>
        <p>
          Save your files. Be ready to trace the first iteration, explain one key
          lookup, and show that all three objects were required for completion.
        </p>
        <p>
          <Link className="text-link" href="/students/learn/s06/">
            What we learned in Python today &rarr;
          </Link>
        </p>
      </>
    ),
  },
];

export default function S06SlidesPage() {
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
            Student slides for session {session.id}. Use these to follow along in
            class or to recap what to try before next time.
          </p>
          <JourneyContext session={session.id} />
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
