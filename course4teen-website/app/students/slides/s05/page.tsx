import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import SiteHeader from "../../../components/SiteHeader";
import SiteFooter from "../../../components/SiteFooter";
import JourneyContext from "../../../components/JourneyContext";
import { classSessions, formatSessionDate } from "../../../../lib/calendar";

const session = classSessions.find((s) => s.id === "S05")!;
const nextSession = classSessions.find((s) => s.id === "S06")!;

export const metadata: Metadata = {
  title: `${session.id} Slides · ${session.title} | Course4Teen`,
  description: `Student slides for Course4Teen session ${session.id}, ${session.title}: an ordered Python list of dialogue lines, indexes [0] and [-1], len(...), and the Moonlit Guide's conversation.`,
  alternates: { canonical: "/students/slides/s05/" },
};

const indexRows = [
  { index: "dialogue[0]", position: "First item", role: "The situation" },
  { index: "dialogue[1]", position: "Second item", role: "The clue (optional)" },
  { index: "dialogue[2]", position: "Third item", role: "The task" },
  { index: "dialogue[-1]", position: "Final item, counted from the end", role: "The task, for two lines or three" },
];

const trailCommand = `explore-package trail \\
  examples/explorer-packages/nova-character \\
  examples/explorer-packages/crystal-lantern \\
  lessons/sessions/s05/student/explorer-package \\
  --player "nova-character:nova" \\
  --mission-id "write-a-short-conversation" \\
  --name "S05 Script a Conversation"`;

type Slide = {
  kicker: string;
  heading: string;
  body: ReactNode;
  hero?: boolean;
};

const slides: Slide[] = [
  {
    kicker: "The Moonlit expedition continues",
    heading: session.title,
    hero: true,
    body: (
      <>
        <p className="slide-lede">
          The Moonlit Guide introduced itself last session, and it has more to
          say. Today you store a conversation as an ordered Python list, and the
          guide gives its briefing one line at a time.
        </p>
        <pre className="slide-code">
          <code>{`dialogue = ["...", "...", "..."]`}</code>
        </pre>
      </>
    ),
  },
  {
    kicker: "Today's mission",
    heading: "M05 · Write a Conversation",
    body: (
      <>
        <p>
          <strong>Mission:</strong> <code>write-a-short-conversation</code>
        </p>
        <p>
          <strong>Learning target:</strong> Create an ordered list of 2–3
          dialogue lines, retrieve its first and final items, use{" "}
          <code>len(...)</code>, and debug order or indexing.
        </p>
        <p>
          The mission is complete when the guide says its final line.
        </p>
      </>
    ),
  },
  {
    kicker: "Warm-up",
    heading: "A tiny story arc",
    body: (
      <>
        <p>
          A short briefing has a beginning and an ending. With three lines, it
          goes:
        </p>
        <ul className="slide-checks">
          <li>
            <strong>Situation:</strong> what the problem is.
          </li>
          <li>
            <strong>Clue:</strong> what to look for (optional).
          </li>
          <li>
            <strong>Task:</strong> what the explorer should do next.
          </li>
        </ul>
        <p>Say your guide&rsquo;s situation and task out loud before you type.</p>
      </>
    ),
  },
  {
    kicker: "Recap from S04",
    heading: "One value, one name",
    body: (
      <>
        <pre className="slide-code">
          <code>{`place = "Moonlit Trail"
greet("Ari")`}</code>
        </pre>
        <ul className="slide-checks">
          <li>
            A <strong>variable</strong> gives one value a name.
          </li>
          <li>
            Last session the guide had <strong>one</strong> greeting. Today it
            has several lines, and their order matters.
          </li>
          <li>Today one name holds the whole conversation.</li>
        </ul>
      </>
    ),
  },
  {
    kicker: "New today",
    heading: "What is a list?",
    body: (
      <>
        <p>
          A <strong>list</strong> holds several items in order, inside square
          brackets, with a comma after each item.
        </p>
        <pre className="slide-code">
          <code>{`dialogue = [
    "Guide: The dark stretch past the ridge won't clear.",
    "Guide: Three old marker-lights never burned out.",
    "Guide: Find those three lights and lead me home.",
]`}</code>
        </pre>
        <p>
          Each item is a string. The list keeps them in the order you wrote
          them.
        </p>
      </>
    ),
  },
  {
    kicker: "Read the positions",
    heading: "dialogue[0] and dialogue[-1]",
    body: (
      <>
        <div className="slide-map-wrap">
          <table className="slide-map">
            <caption className="slide-map-caption">Each index picks one item</caption>
            <thead>
              <tr>
                <th scope="col">Index</th>
                <th scope="col">Position</th>
                <th scope="col">In a briefing</th>
              </tr>
            </thead>
            <tbody>
              {indexRows.map((row) => (
                <tr key={row.index}>
                  <th scope="row">
                    <code>{row.index}</code>
                  </th>
                  <td>{row.position}</td>
                  <td>{row.role}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p>
          Python counts from <strong>0</strong>. A negative index counts from
          the end, so <code>[-1]</code> is always the final line.
        </p>
      </>
    ),
  },
  {
    kicker: "Count the items",
    heading: "len(dialogue)",
    body: (
      <>
        <p>
          <code>len(...)</code> counts the items in a list.
        </p>
        <pre className="slide-code">
          <code>{`print(len(dialogue))`}</code>
        </pre>
        <pre className="slide-code slide-output">
          <code>3</code>
        </pre>
        <p>
          Three items have the indexes 0, 1, and 2. The length is one more than
          the last index.
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
          <code>{`dialogue = [
    "TODO: write an opening line",
    "TODO: write an ending line",
]

# TODO: print the first line with index 0.
# TODO: print the final line with index -1.
print(len(dialogue))`}</code>
        </pre>
        <pre className="slide-code">
          <code>python lessons/sessions/s05/student/starter.py</code>
        </pre>
        <p>Before you change anything, it prints only the length:</p>
        <pre className="slide-code slide-output">
          <code>2</code>
        </pre>
      </>
    ),
  },
  {
    kicker: "Predict before running",
    heading: "Write four predictions first",
    body: (
      <>
        <p>Before you run anything, write down:</p>
        <ol className="slide-steps">
          <li>your exact first line,</li>
          <li>your exact final line,</li>
          <li>the list length, and</li>
          <li>what the guide will say if you press E again after its final line.</li>
        </ol>
      </>
    ),
  },
  {
    kicker: "Core path",
    heading: "Lines, indexes, run",
    body: (
      <>
        <ol className="slide-steps">
          <li>
            Replace both TODO strings: an opening line (the situation) and an
            ending line (a task). Add a middle clue only if it helps the story.
          </li>
          <li>
            Add <code>print(dialogue[0])</code> and{" "}
            <code>print(dialogue[-1])</code> where the TODO comments are.
          </li>
          <li>Run the file and compare the output with your predictions.</li>
          <li>
            <strong>Checkpoint:</strong> show your first line, final line, and
            length.
          </li>
        </ol>
        <p>With the three lines from the list slide, the output is:</p>
        <pre className="slide-code slide-output">
          <code>{`Guide: The dark stretch past the ridge won't clear.
Guide: Find those three lights and lead me home.
3`}</code>
        </pre>
      </>
    ),
  },
  {
    kicker: "Deliberate debugging",
    heading: "Ask for dialogue[3]",
    body: (
      <>
        <ol className="slide-steps">
          <li>
            Temporarily change <code>dialogue[-1]</code> to{" "}
            <code>dialogue[3]</code>.
          </li>
          <li>Predict what happens before you run it.</li>
          <li>Run it. Read the final line of the traceback:</li>
        </ol>
        <pre className="slide-code slide-output">
          <code>IndexError: list index out of range</code>
        </pre>
        <ol className="slide-steps" start={4}>
          <li>
            Move upward to the line naming <code>starter.py</code>.
          </li>
          <li>
            Restore <code>dialogue[-1]</code> and rerun successfully.
          </li>
        </ol>
        <p>
          A three-line list has positions 0, 1, and 2. There is no position 3.
        </p>
      </>
    ),
  },
  {
    kicker: "Order carries the meaning",
    heading: "Swap two lines",
    body: (
      <>
        <p>
          Swap two strings in your list. Predict how the story changes, run it,
          and read your first and final lines.
        </p>
        <p>
          Then restore the intended order: <strong>situation</strong> &rarr;{" "}
          <strong>clue</strong> &rarr; <strong>task</strong>. A task before the
          situation makes the briefing confusing.
        </p>
      </>
    ),
  },
  {
    kicker: "The bridge to the world",
    heading: "Python list, YAML conversation",
    body: (
      <>
        <div className="slide-map-wrap">
          <table className="slide-map">
            <caption className="slide-map-caption">From your list to the Trail</caption>
            <thead>
              <tr>
                <th scope="col">Python value</th>
                <th scope="col">YAML field</th>
                <th scope="col">What you see</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <th scope="row">
                  Ordered <code>dialogue</code> strings
                </th>
                <td>
                  <code>conversation</code>
                </td>
                <td>One line per E press</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p>
          Copy only the spoken text, in the same order, without the{" "}
          <code>Guide: </code> label. YAML drives the Trail:
        </p>
        <pre className="slide-code">
          <code>{`# lessons/sessions/s05/student/explorer-package/character/guide.yaml
name: "Moonlit Guide"
conversation:
  - "The dark stretch past the ridge won't clear."
  - "Three old marker-lights never burned out."
  - "Find those three lights and lead me home."`}</code>
        </pre>
      </>
    ),
  },
  {
    kicker: "Validate first",
    heading: "Check the package",
    body: (
      <>
        <pre className="slide-code">
          <code>explore-package validate lessons/sessions/s05/student/explorer-package</code>
        </pre>
        <p>
          Look for <code>valid: ...</code>. Keep 2 or 3 nonblank lines. If
          validation fails, fix only the first reported issue and try again.
        </p>
      </>
    ),
  },
  {
    kicker: "Launch the Trail",
    heading: "Back to the Moonlit Guide",
    body: (
      <>
        <pre className="slide-code">
          <code>{trailCommand}</code>
        </pre>
        <p>
          Today&rsquo;s Trail is the same painted Moon Meadow as S04, and the
          Moonlit Guide waits in the same spot. A small floating speech cue
          stays over the guide until it has said its final line.
        </p>
      </>
    ),
  },
  {
    kicker: "Talk through every line",
    heading: "Talk to Moonlit Guide",
    body: (
      <>
        <ol className="slide-steps">
          <li>
            Walk Nova up to the guide. The prompt reads{" "}
            <strong>Talk to Moonlit Guide</strong>.
          </li>
          <li>
            Press <kbd>E</kbd> once per line. Each line appears whole in the
            guide&rsquo;s speech bubble, under its{" "}
            <strong>Moonlit Guide</strong> name tag.
          </li>
          <li>
            <strong>Checkpoint:</strong> do the lines appear in your list&rsquo;s
            order?
          </li>
        </ol>
        <p>The bottom line of the screen repeats each line too.</p>
      </>
    ),
  },
  {
    kicker: "Mission success",
    heading: "M05 complete",
    body: (
      <>
        <p>
          When the guide says its final line, watch the{" "}
          <strong>Mission state</strong> row change to <strong>Complete</strong>.
        </p>
        <p>
          Now test your fourth prediction: press <kbd>E</kbd> one more time. The
          conversation starts again at line one, and M05 stays complete.
        </p>
        <p>
          The Crystal Lantern still glows in the meadow, but it is not
          today&rsquo;s target: M05 completes by talking through the
          guide&rsquo;s final line.
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
          <strong>Counting from 0:</strong> the first line is{" "}
          <code>[0]</code>, not <code>[1]</code>.
        </li>
        <li>
          <strong>Commas:</strong> every line in the list ends with a comma.
          A missing comma joins two strings into one.
        </li>
        <li>
          <strong>Same order:</strong> the YAML <code>conversation</code> keeps
          the order you tested in Python.
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
          <strong>Support:</strong> keep two lines. On paper, label them index
          0 and index 1 before you add the print expressions. Ask the teacher to
          point to the list position rather than paste a finished file.
        </p>
        <p>
          <strong>Extension:</strong> add one middle clue to a two-line
          conversation, so it reads situation, clue, task. Stay within 2–3
          lines.
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
        &ldquo;Why does index 3 not exist in my three-line list?&rdquo; AI may
        explain one indexing error or say whether your conversation is clear. It
        may not write or reorder your conversation. Record your intent,
        prediction, exact question, suggestion tested, accepted or rejected
        change, and your own explanation.
      </p>
    ),
  },
  {
    kicker: "Exit check",
    heading: "Three quick answers",
    body: (
      <ul className="slide-checks">
        <li>
          <strong>Indexes:</strong> Which index shows your first line? Which
          shows your final line, whether you have two lines or three?
        </li>
        <li>
          <strong>Length:</strong> What did <code>len(dialogue)</code> print,
          and why?
        </li>
        <li>
          <strong>Debugging:</strong> Why did <code>dialogue[3]</code> raise an{" "}
          <code>IndexError</code>, and how did you fix it?
        </li>
      </ul>
    ),
  },
  {
    kicker: "Looking ahead",
    heading: `${nextSession.id} · ${nextSession.title}`,
    body: (
      <p>
        That&rsquo;s the next session on the class calendar. Keep today&rsquo;s
        list ready to explain.
      </p>
    ),
  },
  {
    kicker: "Close",
    heading: "Wrap up S05",
    body: (
      <>
        <p>
          Save your files. Be ready to read your conversation aloud in order and
          to explain <code>[0]</code>, <code>[-1]</code>, and{" "}
          <code>len(...)</code> in your own code. A correct explanation matters
          more than finishing every step.
        </p>
        <p>
          <Link className="text-link" href="/students/learn/s05/">
            What we learned in Python today &rarr;
          </Link>
        </p>
      </>
    ),
  },
];

export default function S05SlidesPage() {
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
