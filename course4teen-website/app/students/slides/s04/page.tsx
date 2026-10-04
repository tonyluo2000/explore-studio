import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import SiteHeader from "../../../components/SiteHeader";
import SiteFooter from "../../../components/SiteFooter";
import JourneyContext from "../../../components/JourneyContext";
import { classSessions, formatSessionDate } from "../../../../lib/calendar";

export const metadata: Metadata = {
  title: "S04 Slides · Introduce a Character | Course4Teen",
  description:
    "Student slides for Course4Teen session S04, Introduce a Character: define and call greet(name), parameters and arguments, and the Moonlit Guide's greeting.",
  alternates: { canonical: "/students/slides/s04/" },
};

const session = classSessions.find((s) => s.id === "S04")!;

const anatomyRows = [
  { part: "def", meaning: "Short for define. It starts a new function." },
  { part: "greet", meaning: "The function name. You use this exact name to call it." },
  { part: "(name)", meaning: "The parameter: a placeholder for the value each call sends in." },
  { part: ":", meaning: "The colon ends the definition line. The body comes next." },
  { part: "    place = ...", meaning: "The body. Every body line is indented by the same four spaces." },
];

const parameterRows = [
  { word: "parameter", where: "In the definition", example: "def greet(name):" },
  { word: "argument", where: "In the call", example: 'greet("Ari")' },
];

const trailCommand = `explore-package trail \\
  examples/explorer-packages/nova-character \\
  examples/explorer-packages/crystal-lantern \\
  lessons/sessions/s04/student/explorer-package \\
  --player "nova-character:nova" \\
  --mission-id "introduce-your-character" \\
  --name "S04 Introduce a Character"`;

type Slide = {
  kicker: string;
  heading: string;
  body: ReactNode;
  hero?: boolean;
};

const slides: Slide[] = [
  {
    kicker: "The Moonlit expedition continues",
    heading: "Introduce a Character",
    hero: true,
    body: (
      <>
        <p className="slide-lede">
          Your Moon Compass&rsquo;s clue led here, to a guide who needs your
          help. Today you write a Python function that greets anyone by name,
          and you give the guide a voice.
        </p>
        <pre className="slide-code">
          <code>{`def greet(name):`}</code>
        </pre>
      </>
    ),
  },
  {
    kicker: "Today's mission",
    heading: "M04 · Give Your Character a Voice",
    body: (
      <>
        <p>
          <strong>Mission:</strong> <code>introduce-your-character</code>
        </p>
        <p>
          <strong>Learning target:</strong> Define and call{" "}
          <code>greet(name)</code>, explain its parameter, and use a traceback
          to repair an argument problem.
        </p>
        <p>
          The mission is complete when you speak to the guide and its greeting
          appears.
        </p>
      </>
    ),
  },
  {
    kicker: "Warm-up",
    heading: "A voice in three words",
    body: (
      <>
        <p>
          Describe your guide&rsquo;s voice in three words. Calm, mysterious,
          and kind? Cheerful, quick, and curious?
        </p>
        <p>
          Keep those words in mind. You will use them when you write the
          guide&rsquo;s greeting.
        </p>
      </>
    ),
  },
  {
    kicker: "Recap from S03",
    heading: "f-strings and calls",
    body: (
      <>
        <pre className="slide-code">
          <code>{`object_name = "Moon Compass"
print(f"The {object_name} glows.")`}</code>
        </pre>
        <ul className="slide-checks">
          <li>
            An <strong>f-string</strong> fills in the value of each variable
            inside its braces.
          </li>
          <li>
            <code>print(...)</code> is a <strong>function call</strong>: a name,
            then parentheses holding the value it works on.
          </li>
          <li>
            Today you write your own function, and call it the same way.
          </li>
        </ul>
      </>
    ),
  },
  {
    kicker: "New today",
    heading: "What is a function?",
    body: (
      <>
        <p>
          A <strong>function</strong> is a named, reusable set of steps. You{" "}
          <strong>define</strong> it once, then <strong>call</strong> it as many
          times as you need.
        </p>
        <pre className="slide-code">
          <code>{`def greet(name):
    place = "Moonlit Trail"
    print(f"Welcome to {place}, {name}!")`}</code>
        </pre>
        <p>
          Defining a function does not run it. Nothing prints until a line
          calls <code>greet</code>.
        </p>
      </>
    ),
  },
  {
    kicker: "Read the definition",
    heading: "def greet(name):",
    body: (
      <div className="slide-map-wrap">
        <table className="slide-map">
          <caption className="slide-map-caption">The parts of a function definition</caption>
          <tbody>
            {anatomyRows.map((row) => (
              <tr key={row.part}>
                <th scope="row">
                  <code>{row.part}</code>
                </th>
                <td>{row.meaning}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    ),
  },
  {
    kicker: "Call the function",
    heading: "greet(\"Ari\")",
    body: (
      <>
        <p>
          A <strong>call</strong> runs the function&rsquo;s body. The value inside
          the parentheses is the <strong>argument</strong>. Python puts it into
          the parameter <code>name</code>.
        </p>
        <pre className="slide-code">
          <code>{`greet("Ari")`}</code>
        </pre>
        <pre className="slide-code slide-output">
          <code>Welcome to Moonlit Trail, Ari!</code>
        </pre>
        <p>
          Inside the body, <code>{"{name}"}</code> becomes <code>Ari</code>. Call
          it again with <code>&quot;Sam&quot;</code>, and the same body greets Sam.
        </p>
      </>
    ),
  },
  {
    kicker: "Two words, two places",
    heading: "Parameter vs. argument",
    body: (
      <>
        <div className="slide-map-wrap">
          <table className="slide-map">
            <caption className="slide-map-caption">Where each word belongs</caption>
            <thead>
              <tr>
                <th scope="col">Word</th>
                <th scope="col">Where it lives</th>
                <th scope="col">Example</th>
              </tr>
            </thead>
            <tbody>
              {parameterRows.map((row) => (
                <tr key={row.word}>
                  <th scope="row">{row.word}</th>
                  <td>{row.where}</td>
                  <td>
                    <code>{row.example}</code>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p>
          <code>name</code> is the parameter. <code>&quot;Ari&quot;</code> is the
          argument. One function body makes a personalized greeting for each
          argument.
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
          <code>{`def greet(name):
    place = "TODO: name your setting"
    print(f"Welcome to {place}, {name}!")


greet("Ari")
# TODO: call greet one more time with a name you choose.`}</code>
        </pre>
        <pre className="slide-code">
          <code>python lessons/sessions/s04/student/starter.py</code>
        </pre>
        <p>Before you change anything, it prints:</p>
        <pre className="slide-code slide-output">
          <code>Welcome to TODO: name your setting, Ari!</code>
        </pre>
        <p>
          The visible TODO and the missing second greeting are on purpose. Both
          are yours to finish.
        </p>
      </>
    ),
  },
  {
    kicker: "Predict before running",
    heading: "Write your two lines first",
    body: (
      <>
        <p>
          Read the first call and write its exact output. Then choose a name for
          your second call and predict the line it will print.
        </p>
        <p className="slide-lede">
          &ldquo;My two lines will be ___ and ___.&rdquo;
        </p>
        <p>Run Python only after both predictions are written down.</p>
      </>
    ),
  },
  {
    kicker: "Core path",
    heading: "Setting, second call, run",
    body: (
      <>
        <ol className="slide-steps">
          <li>
            Replace the TODO value of <code>place</code> with your setting name.
          </li>
          <li>
            Add one second <code>greet(&quot;...&quot;)</code> call with a name
            you choose.
          </li>
          <li>Run the file and compare the output with your prediction.</li>
          <li>
            <strong>Checkpoint:</strong> explain function, parameter, and
            argument using your two output lines.
          </li>
        </ol>
        <p>
          With <code>place = &quot;Moonlit Trail&quot;</code> and a second call{" "}
          <code>greet(&quot;Sam&quot;)</code>, the output is:
        </p>
        <pre className="slide-code slide-output">
          <code>{`Welcome to Moonlit Trail, Ari!
Welcome to Moonlit Trail, Sam!`}</code>
        </pre>
      </>
    ),
  },
  {
    kicker: "The bridge to the world",
    heading: "Python greeting, YAML greeting",
    body: (
      <>
        <div className="slide-map-wrap">
          <table className="slide-map">
            <caption className="slide-map-caption">From your function to the Trail</caption>
            <thead>
              <tr>
                <th scope="col">Python idea</th>
                <th scope="col">YAML field</th>
                <th scope="col">What you see</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <th scope="row">
                  Personalized <code>greet(name)</code> output
                </th>
                <td>
                  <code>greeting</code>
                </td>
                <td>The guide speaks one authored greeting</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p>
          The function runs on your computer. The guide&rsquo;s greeting is
          plain text in YAML, and YAML drives the Trail:
        </p>
        <pre className="slide-code">
          <code>{`# lessons/sessions/s04/student/explorer-package/character/guide.yaml
name: "Moonlit Guide"
greeting: "I'm the Moonlit Guide, explorer — the trail beyond this ridge has gone dark, and I need your help finding a way through."`}</code>
        </pre>
      </>
    ),
  },
  {
    kicker: "Your story choice",
    heading: "Write the guide's greeting",
    body: (
      <>
        <p>
          Personalize the <code>greeting</code> in <strong>one sentence</strong>{" "}
          that tells:
        </p>
        <ul className="slide-checks">
          <li>
            <strong>who</strong> the guide is,
          </li>
          <li>
            <strong>what</strong> the trail problem is, and
          </li>
          <li>
            <strong>what help</strong> the guide needs.
          </li>
        </ul>
        <p>
          Use your three voice words. Keep the greeting about as long as the
          example: a very long greeting ends in <code>&hellip;</code> in the
          speech bubble.
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
          <code>explore-package validate lessons/sessions/s04/student/explorer-package</code>
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
    heading: "Meet the Moonlit Guide",
    body: (
      <>
        <pre className="slide-code">
          <code>{trailCommand}</code>
        </pre>
        <p>
          Today&rsquo;s Trail is the same painted Moon Meadow as S02 and S03.
          The Moonlit Guide stands in it: a hooded moon-sage with a
          crescent-moon staff. A small floating speech cue marks the guide until
          you speak to it.
        </p>
      </>
    ),
  },
  {
    kicker: "Speak to the guide",
    heading: "Talk to Moonlit Guide",
    body: (
      <>
        <ol className="slide-steps">
          <li>
            Walk Nova up to the guide. The prompt reads{" "}
            <strong>Talk to Moonlit Guide</strong>.
          </li>
          <li>
            Press <kbd>E</kbd>. The whole greeting appears in the guide&rsquo;s
            speech bubble, under its <strong>Moonlit Guide</strong> name tag.
          </li>
          <li>
            <strong>Checkpoint:</strong> read your exact greeting from the
            bubble, and report the M04 result.
          </li>
        </ol>
        <p>
          The bottom line of the screen repeats the greeting and may end in{" "}
          <code>&hellip;</code> when it is too long to fit. Read the greeting
          from the bubble.
        </p>
      </>
    ),
  },
  {
    kicker: "Mission success",
    heading: "M04 complete",
    body: (
      <>
        <p>
          Speaking to the guide completes M04. Watch the{" "}
          <strong>Mission state</strong> row change to <strong>Complete</strong>.
        </p>
        <p>
          The Crystal Lantern still glows in the meadow, but it is not
          today&rsquo;s target. You do not need to visit it: M04 completes by
          talking to the guide.
        </p>
      </>
    ),
  },
  {
    kicker: "Deliberate debugging",
    heading: "Call greet() with no argument",
    body: (
      <>
        <ol className="slide-steps">
          <li>Save your working second call somewhere in your notes.</li>
          <li>Temporarily replace it with a call that has no argument:</li>
        </ol>
        <pre className="slide-code">
          <code>{`greet()`}</code>
        </pre>
        <ol className="slide-steps" start={3}>
          <li>Predict the final line of the traceback before running Python.</li>
          <li>Run it. Read the final line for the error type:</li>
        </ol>
        <pre className="slide-code slide-output">
          <code>{`TypeError: greet() missing 1 required positional argument: 'name'`}</code>
        </pre>
        <ol className="slide-steps" start={5}>
          <li>
            Move upward to the first line naming <code>starter.py</code> and its
            line number.
          </li>
          <li>Restore a call with one name and rerun successfully.</li>
        </ol>
        <p>
          Explain the fix using the words <strong>function</strong>,{" "}
          <strong>parameter</strong>, and <strong>argument</strong>.
        </p>
      </>
    ),
  },
  {
    kicker: "Common slips",
    heading: "Three things to check",
    body: (
      <ul className="slide-checks">
        <li>
          <strong>Indentation:</strong> both lines in the function body use the
          same four spaces.
        </li>
        <li>
          <strong>Function name:</strong> the call must match the definition
          exactly: <code>greet</code>.
        </li>
        <li>
          <strong>Argument:</strong> one name string belongs inside the
          call&rsquo;s parentheses. Do not add another parameter to hide an
          error.
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
          <strong>Support:</strong> compare your code with this recovery shape,
          then type only the missing pieces:
        </p>
        <pre className="slide-code">
          <code>{`place = "Moonlit Trail"
print(f"Welcome to {place}, {name}!")
greet("Sam")`}</code>
        </pre>
        <p>
          The first two lines belong inside the function; the call goes after
          it. Ask the teacher to point to the location rather than paste a
          finished file.
        </p>
        <p>
          <strong>Extension:</strong> add a third call to the same function
          with a new name, and predict its exact output first. Do not add
          another character or package field.
        </p>
      </>
    ),
  },
  {
    kicker: "Using AI on this mission",
    heading: "Bounded questions, not full solutions",
    body: (
      <p>
        Explain your intent and write your prediction first. A good question is
        &ldquo;What does the final line of this traceback say is missing?&rdquo;
        AI may explain a traceback. It may not write your correction or your
        guide&rsquo;s greeting. Record your intent, prediction, exact question,
        suggestion tested, accepted or rejected change, and your own
        explanation.
      </p>
    ),
  },
  {
    kicker: "Exit check",
    heading: "Three quick answers",
    body: (
      <ul className="slide-checks">
        <li>
          <strong>Functions:</strong> In <code>def greet(name):</code>, which
          word is the parameter? In your second call, what is the argument?
        </li>
        <li>
          <strong>Output:</strong> Why do your two calls print two different
          lines from one function body?
        </li>
        <li>
          <strong>Debugging:</strong> What did the final traceback line say was
          missing when you called <code>greet()</code>? How did you fix it?
        </li>
      </ul>
    ),
  },
  {
    kicker: "Looking ahead",
    heading: "S05 · Script a Conversation",
    body: (
      <p>
        Your guide has introduced itself. Next session, the guide has more to
        say, and you help script the conversation.
      </p>
    ),
  },
  {
    kicker: "Close",
    heading: "Wrap up S04",
    body: (
      <>
        <p>
          Save your files. Be ready to explain the parameter and the argument in
          your own code, and to read your guide&rsquo;s greeting aloud. A correct
          explanation matters more than finishing every step.
        </p>
        <p>
          <Link className="text-link" href="/students/learn/s04/">
            What we learned in Python today &rarr;
          </Link>
        </p>
      </>
    ),
  },
];

export default function S04SlidesPage() {
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
