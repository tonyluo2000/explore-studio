import type { Metadata } from "next";
import type { ReactNode } from "react";
import Image from "next/image";
import Link from "next/link";
import SiteHeader from "../../../components/SiteHeader";
import SiteFooter from "../../../components/SiteFooter";
import JourneyContext from "../../../components/JourneyContext";
import PythonJourney from "../../../components/PythonJourney";
import { classSessions, formatSessionDate } from "../../../../lib/calendar";

const session = classSessions.find((item) => item.id === "S09")!;
export const metadata: Metadata = {
  title: `${session.id} Slides · ${session.title} | Course4Teen`,
  description: "Count sparks, repair an off-by-one loop, and verify the exact success interaction in Moon Meadow.",
  alternates: { canonical: "/students/slides/s09/" },
};

const trailCommand = `explore-package trail examples/explorer-packages/nova-character lessons/sessions/s09/student/explorer-package --player "nova-character:nova" --mission-id "count-object-interactions" --name "S09 Power Up a Device"`;

const slides: { heading: string; body: ReactNode }[] = [
  { heading: "S09 · Power Up a Device", body: <p className="slide-lede">Nova reaches the Storm Engine on the observatory approach. Each spark is one real charging action. Power it up for the next readiness check.</p> },
  { heading: "Two journeys, one mission", body: <p>Explorer Journey: the Guardian has led us to the device. Python Journey: use integers from S02 and loops from S06. Today is step 9 / 30.</p> },
  { heading: "Today in Python: counters", body: <p>Keep an integer counter, update it in a simple loop, predict exact success, diagnose an off-by-one mistake, and write one basic assertion.</p> },
  { heading: "Review integers", body: <><pre className="slide-code"><code>{`goal = 3
count = 0`}</code></pre><p>Both values are integers: whole numbers. Zero means no charging actions yet. The goal is the intended number of actions.</p></> },
  { heading: "One interaction = one update", body: <><pre className="slide-code"><code>count = count + 1</code></pre><p>Read the old value, add one, then assign the result back to count. One successful E interaction in Trail adds one spark.</p></> },
  { heading: "Predict exact success", body: <p>Before running Python or Trail, predict the count after interactions 1, 2, 3, and 4. Circle the exact interaction where success should first appear for goal 3.</p> },
  { heading: "Trace the count", body: <><pre className="slide-code"><code>{`Start          0
Interaction 1  1
Interaction 2  2
Interaction 3  3 ← first success
Interaction 4  4`}</code></pre><p>Interaction 2 is one spark short. The third update reaches the goal.</p></> },
  { heading: "Run the canonical starter", body: <><pre className="slide-code"><code>{`goal = 3
count = 0

for interaction_number in range(1, goal + 1):
    count = count + 1
    print(interaction_number, count)

# TODO: add one assertion that proves count reached goal.`}</code></pre><pre className="slide-code"><code>python lessons/sessions/s09/student/starter.py</code></pre><p>The starter loop is correct. range stops before its second number, so this loop visits 1, 2, and 3. The assertion is your unfinished task.</p></> },
  { heading: "Create and find the off-by-one bug", body: <><p>First add your assertion below the TODO. Then temporarily shorten only the loop stop:</p><pre className="slide-code"><code>for interaction_number in range(1, goal):</code></pre><p>Predict the final count, then run. Only 1 and 2 print; the assertion fails. Off-by-one means one update too few or too many.</p></> },
  { heading: "Repair the smallest line", body: <><pre className="slide-code"><code>for interaction_number in range(1, goal + 1):</code></pre><p>Restore the stop value, rerun, and check all three updates. Explain why stopping before 4 includes 3.</p></> },
  { heading: "Explain one assertion", body: <><p>Write a check that the final count equals the goal. Try it yourself before reading the shape below.</p><details><summary>Compare your assertion</summary><pre className="slide-code"><code>assert count == goal</code></pre></details><p>A passing assertion is silent. A false check raises AssertionError. It protects the expected final count and catches the shortened loop ending at 2. No testing framework is needed.</p></> },
  { heading: "Python → YAML → Trail", body: <ul className="slide-checks"><li>Local Python models repeated counting and update logic.</li><li>Package YAML declares the counter goal and goal-reached message.</li><li>Trail owns the actual interaction count during the session. Student Python does not execute inside Trail.</li></ul> },
  { heading: "Read the authored counter", body: <><pre className="slide-code"><code>{`counter:
  goal: 3
  when_goal_reached: "The storm engine is fully charged — ready for the reading!"`}</code></pre><p>Open objects/storm-engine.yaml. Keep your goal from 2 through 5. Personalize the device and message; keep the package identity. The authored purple color stays visible in the device.</p></> },
  { heading: "Validate the package", body: <><pre className="slide-code"><code>explore-package validate lessons/sessions/s09/student/explorer-package</code></pre><pre className="slide-code slide-output"><code>valid: storm-engine 0.1.0</code></pre><p>Fix validation errors before launching.</p></> },
  { heading: "Launch the actual S09 Trail", body: <><pre className="slide-code"><code>{trailCommand}</code></pre><p>Run the complete one-line command from the Course Kit folder. Nova arrives in Moon Meadow near the Storm Engine. Move toward its prompt.</p></> },
  { heading: "Add sparks one at a time", body: <p>At the readable Inspect Storm Engine prompt, press E once. Record count 1. Release and press again for each update. Compare every count with your prediction.</p> },
  { heading: "Watch the charge grow", body: <p>More charge cells illuminate on every update. The core grows brighter. At the goal, all cells light and the lightning core and sparks appear. Use the cell shapes and numeric count as well as color.</p> },
  { heading: "Confirm exact completion", body: <><p>For goal 3, the third interaction displays the authored goal-reached message and completes M09 · Power It Up. No extra press is needed.</p><Image src="/journey/s09/hero.webp" alt="Nova beside the fully powered purple Storm Engine, with Count 3 / 3 and mission complete." width={960} height={640} className="h-auto max-w-full rounded-xl" /><p>Optional: one later press continues counting and keeps the mission complete. There is no reset, decrement, or cap.</p></> },
  { heading: "Why one spark short is not enough", body: <p>At count 2, one charge cell is still empty and the mission is incomplete. Compare that with exact goal 3. Explain why a loop doing only two updates cannot satisfy your assertion.</p> },
  { heading: "Explain your tested repair", body: <><ul className="slide-checks"><li>Name the integer counter and its update.</li><li>Explain range and the off-by-one repair.</li><li>Explain what your assertion protects.</li><li>Separate Python, YAML, and Trail state.</li></ul><p>The powered device prepares the observatory in our story; its runtime count does not carry into a later session.</p><p><Link className="text-link" href="/students/learn/s09/">Review the Python notes →</Link></p><p>Next: S10 · Check the Boundary · Sat, Nov 28, 2026.</p></> },
];

export default function S09SlidesPage() {
  return <>
    <a className="skip-link" href="#main">Skip to content</a>
    <SiteHeader />
    <main id="main">
      <section className="section slides-hero">
        <p className="kicker">{session.id} &middot; {formatSessionDate(session.date)}</p>
        <h1>{session.title}</h1>
        <p className="calendar-lede">Count repeated actions, repair an off-by-one mistake, and power the observatory device with exactly enough sparks.</p>
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
