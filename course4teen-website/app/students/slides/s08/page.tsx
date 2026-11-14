import type { Metadata } from "next";
import type { ReactNode } from "react";
import Image from "next/image";
import Link from "next/link";
import SiteHeader from "../../../components/SiteHeader";
import SiteFooter from "../../../components/SiteFooter";
import JourneyContext from "../../../components/JourneyContext";
import PythonJourney from "../../../components/PythonJourney";
import { classSessions, formatSessionDate } from "../../../../lib/calendar";

const session = classSessions.find((item) => item.id === "S08")!;
export const metadata: Metadata = {
  title: `${session.id} Slides · ${session.title} | Course4Teen`,
  description: "Predict and repair an if/else, then test both Gate Guardian responses in Moon Meadow.",
  alternates: { canonical: "/students/slides/s08/" },
};

const trailCommand = `explore-package trail examples/explorer-packages/nova-character lessons/sessions/s08/student/explorer-package --player "nova-character:nova" --mission-id "respond-to-object-state" --name "S08 Build an If/Else Guardian"`;

const slides: { heading: string; body: ReactNode }[] = [
  {
    heading: "Follow the Sky Lantern signal",
    body: <p className="slide-lede">The signal leads Nova to the Cloud Gate. Can the Guardian give Nova a clue when the switch is off and a welcome when it is on?</p>,
  },
  {
    heading: "Predict both responses",
    body: <>
      <p>Before running Python, write the response that should go with each input. Read your rule aloud using “If … then … otherwise …”.</p>
      <pre className="slide-code"><code>{`guardian_response(False) → __________________
guardian_response(True)  → __________________`}</code></pre>
    </>,
  },
  {
    heading: "Run the starter",
    body: <>
      <pre className="slide-code"><code>{`def guardian_response(is_on):
    if not is_on:
        return "The portal is glowing!"
    else:
        return "The portal is sleeping."`}</code></pre>
      <pre className="slide-code"><code>python lessons/sessions/s08/student/starter.py</code></pre>
      <p>The starter calls the function with <code>False</code> first. Trace which branch it takes. How does <code>not</code> change that input?</p>
    </>,
  },
  {
    heading: "Repair the condition",
    body: <>
      <p>Change the condition to <code>if is_on:</code> and run both cases again. The <code>if</code> block runs for <code>True</code> and the <code>else</code> block runs for <code>False</code>.</p>
      <pre className="slide-code slide-output"><code>{`The portal is sleeping.
The portal is glowing!`}</code></pre>
      <p>Point to the <code>return</code> line that produced each response.</p>
    </>,
  },
  {
    heading: "Connect the Guardian to the switch",
    body: <>
      <p>The Python function models a decision. The Trail reads its own switch state and chooses a response from <code>character/gate-guardian.yaml</code>.</p>
      <ul className="slide-checks">
        <li><code>{'object_id: "sky-switch"'}</code> links the Guardian to the switch in the same package.</li>
        <li><code>when_off</code> gives Nova a clue. Keep the Sky Switch in your clue.</li>
        <li><code>when_on</code> gives Nova a welcome.</li>
      </ul>
    </>,
  },
  {
    heading: "Validate and launch Moon Meadow",
    body: <>
      <pre className="slide-code"><code>explore-package validate lessons/sessions/s08/student/explorer-package</code></pre>
      <pre className="slide-code slide-output"><code>valid: cloud-gate 0.1.0</code></pre>
      <pre className="slide-code"><code>{trailCommand}</code></pre>
      <p>Copy the complete launch line. Nova starts near the Guardian. Move toward the talk prompt and press <strong>E</strong>.</p>
    </>,
  },
  {
    heading: "Hear the clue, then test it",
    body: <>
      <ol className="slide-checks">
        <li>Talk to the Guardian with the switch OFF. Read the clue and look for <strong>Responses 1 / 2</strong>.</li>
        <li>Walk left to the Sky Switch and press <strong>E</strong> at the prompt. Look for its yellow glow.</li>
        <li>Return to the Guardian and press <strong>E</strong>. Read the new line and look for <strong>Responses 2 / 2</strong>.</li>
      </ol>
      <Image
        src="/journey/s08/guardian-off.webp"
        alt="The Gate Guardian asks Nova to wake the Sky Switch. The HUD shows Responses 1 / 2."
        width={960}
        height={640}
        className="h-auto max-w-full rounded-xl"
      />
    </>,
  },
  {
    heading: "Show both branches",
    body: <>
      <p>M08 completes after you hear both responses. Nova can walk past the Guardian in either state. The Guardian’s dialogue tells the story of the gate opening.</p>
      <p>Write down both lines and explain which state selected each one. If you use AI, ask it to compare your predictions with your results after you explain the condition.</p>
      <p><Link className="text-link" href="/students/learn/s08/">Review the Python notes →</Link></p>
    </>,
  },
];

export default function S08SlidesPage() {
  return <>
    <a className="skip-link" href="#main">Skip to content</a>
    <SiteHeader />
    <main id="main">
      <section className="section slides-hero">
        <p className="kicker">{session.id} &middot; {formatSessionDate(session.date)}</p>
        <h1>{session.title}</h1>
        <p className="calendar-lede">Predict two branches, fix an inverted condition, and hear both answers at the Cloud Gate.</p>
        <div className="journey-companions">
          <JourneyContext session={session.id} />
          <PythonJourney session={session.id} mode="compact" />
        </div>
      </section>
      <section className="section slide-deck">
        {slides.map(({ heading, body }, index) => (
          <article className={index === 0 ? "slide-card slide-hero-card" : "slide-card"} key={heading}>
            <p className="kicker">{session.id} · {index + 1} / {slides.length}</p>
            <h2>{heading}</h2>
            <div className="slide-body">{body}</div>
          </article>
        ))}
      </section>
    </main>
    <SiteFooter />
  </>;
}
