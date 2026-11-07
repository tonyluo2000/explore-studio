import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import SiteHeader from "../../../components/SiteHeader";
import SiteFooter from "../../../components/SiteFooter";
import JourneyContext from "../../../components/JourneyContext";
import PythonJourney from "../../../components/PythonJourney";
import { classSessions, formatSessionDate } from "../../../../lib/calendar";

const session = classSessions.find((s) => s.id === "S07")!;
const nextSession = classSessions.find((s) => s.id === "S08")!;
export const metadata: Metadata = {
  title: `${session.id} Slides · ${session.title} | Course4Teen`,
  description: "Boolean state: predict, repair an assignment, and toggle the Sky Lantern in Moon Meadow.",
  alternates: { canonical: "/students/slides/s07/" },
};
const trailCommand = `explore-package trail examples/explorer-packages/nova-character lessons/sessions/s07/student/explorer-package --player "nova-character:nova" --mission-id "toggle-an-object-state" --name "S07 Create a Two-State Prop"`;
type Slide = { heading: string; body: ReactNode };
const slides: Slide[] = [
  { heading: "S07 · Create a Two-State Prop", body: <><p className="slide-lede">Wind Flower pointed toward a gate hidden in the sky. The <strong>Sky Lantern</strong> is our signal for that gate.</p><p>M07 · Flip a Magic Switch. Use Python to predict two states, then observe the lantern in the polished Moon Meadow Trail.</p></> },
  { heading: "Python Journey so far", body: <p>Output and strings → variables and basic types → f-strings → functions → lists → dictionaries and loops. Today, add <strong>Boolean state</strong>. Follow the session-local Python Journey above.</p> },
  { heading: "Today in Python: Booleans & state", body: <p>Represent two states with a Boolean variable and predict how assignment changes that state. A state is the value something holds at a particular moment.</p> },
  { heading: "False and True", body: <><p>A Boolean has two values: <code>False</code> and <code>True</code>. Capital letters matter. Our lesson uses False for OFF and True for ON.</p><pre className="slide-code"><code>{`off_color = "blue"
on_color = "gold"`}</code></pre></> },
  { heading: "is_on stores one state", body: <><pre className="slide-code"><code>{`is_on = False`}</code></pre><p>Assignment stores False in the local variable <code>is_on</code>. It starts OFF. The two color strings are labels, not instructions that change state.</p></> },
  { heading: "Predict the 4-row trace", body: <><p>Fill the blanks before running Python or the Trail.</p><pre className="slide-code slide-output"><code>{`Observation       is_on       color
Start             False       blue
Interaction 1     ______      ______
Interaction 2     ______      ______
Interaction 3     ______      ______`}</code></pre></> },
  { heading: "Find the starter bug", body: <><pre className="slide-code"><code>{`off_color = "blue"
on_color = "gold"

is_on = False
print(is_on, off_color)

# TODO: change the state before the second observation.
is_on = False
print(is_on, on_color)`}</code></pre><pre className="slide-code"><code>python lessons/sessions/s07/student/starter.py</code></pre><p>Run the starter. Predict the second observation.</p><pre className="slide-code slide-output"><code>{`False blue
False gold`}</code></pre></> },
  { heading: "Printing a color does not change state", body: <p>The second line prints gold but leaves <code>is_on = False</code>. Printing <code>on_color</code> does not change state. Python reports exactly the two values you asked for; it raises no exception here.</p> },
  { heading: "Repair the assignment", body: <><p>Replace only the second False with True before the second observation.</p><pre className="slide-code"><code>{`is_on = True
print(is_on, on_color)`}</code></pre><p>Which line changes state? Which line only reads it?</p></> },
  { heading: "Check the repaired output", body: <><pre className="slide-code slide-output"><code>{`False blue
True gold`}</code></pre><p>Point to the assignment responsible for each Boolean value.</p></> },
  { heading: "Python → YAML → Trail", body: <ul className="slide-checks"><li>Local Python models the idea; it does not control the Trail.</li><li>YAML declares the supported, distinct toggle colors.</li><li>Trail owns runtime session state. Every toggle starts OFF.</li></ul> },
  { heading: "Declare the two colors", body: <><pre className="slide-code"><code>{`toggle:
  off_color: "blue"
  on_color: "gold"`}</code></pre><p><code>toggle.off_color</code> supplies OFF; <code>toggle.on_color</code> supplies ON. Keep the Sky Lantern object at x 360, y 300. Personalize supported colors and messages, then validate.</p></> },
  { heading: "Validate the package", body: <><pre className="slide-code"><code>explore-package validate lessons/sessions/s07/student/explorer-package</code></pre><pre className="slide-code slide-output"><code>valid: sky-lantern-switch 0.1.0</code></pre><p>Read any file and field named by the validator. Fix YAML separately from the local Python assignment.</p></> },
  { heading: "Launch S07 Trail", body: <><pre className="slide-code"><code>{trailCommand}</code></pre><p>Copy the whole one-line command. Nova starts near the Sky Lantern in Moon Meadow. Move closer until the Inspect Sky Lantern prompt appears; press <strong>E</strong>.</p></> },
  { heading: "Observe OFF → ON → OFF → ON", body: <><pre className="slide-code slide-output"><code>{`Start          False  OFF  blue
Interaction 1  True   ON   gold
Interaction 2  False  OFF  blue
Interaction 3  True   ON   gold`}</code></pre><p>OFF has dim, cool glass. ON has a bright core, a larger glow, and rising sparks. Compare every row with your prediction.</p><p>The authored near message says “The lantern waits for a spark — one flame could reach the gate above.” The interaction message says “Click! The lantern changes.” These fixed messages do not read state.</p></> },
  { heading: "What M07 completion means", body: <><p>M07 completes after the toggle changes at least once. After the first change it stays complete through OFF and ON.</p><p>Final ON/gold is a story target, not mission-checked. Leave the lantern lit and show your teacher; confirm it by observation. Completion does not verify the final state.</p></> },
  { heading: "Explain what changed", body: <><ul className="slide-checks"><li>Explain False → True → False → True.</li><li>Name the assignment you repaired.</li><li>Separate local Python, YAML colors, and Trail state.</li><li>Show why M07 remains complete after interaction 2.</li></ul><p>Save your work and explain your prediction and tested repair. Use the task card for the AI receipt and optional Git close.</p><p><Link className="text-link" href="/students/learn/s07/">What we learned in Python today →</Link></p></> },
  { heading: `${nextSession.id} · ${nextSession.title}`, body: <p>{formatSessionDate(nextSession.date)}. Our signal points toward the hidden gate. The next session is coming soon.</p> },
];

export default function S07SlidesPage() {
  return <>
    <a className="skip-link" href="#main">Skip to content</a>
    <SiteHeader />
    <main id="main">
      <section className="section slides-hero">
        <p className="kicker">{session.id} &middot; {formatSessionDate(session.date)}</p>
        <h1>{session.title}</h1>
        <p className="calendar-lede">Predict two states, repair an assignment, and send a skyward signal.</p>
        <div className="journey-companions">
          <JourneyContext session={session.id} />
          <PythonJourney session={session.id} mode="compact" />
        </div>
      </section>
      <section className="section slide-deck">{slides.map((slide, i) => <article className={i === 0 ? "slide-card slide-hero-card" : "slide-card"} key={slide.heading}>
        <p className="kicker">S07 · {i + 1} / {slides.length}</p>
        <h2>{slide.heading}</h2><div className="slide-body">{slide.body}</div>
      </article>)}</section>
    </main>
    <SiteFooter />
  </>;
}
